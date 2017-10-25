"""
Various RNN decoders.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# pylint: disable=no-name-in-module, too-many-arguments, too-many-locals

import collections

import tensorflow as tf
from tensorflow.contrib.seq2seq import AttentionWrapper
from tensorflow.python.framework import tensor_shape, dtypes

from txtgen.modules.decoders.rnn_decoder_base import RNNDecoderBase
from txtgen.core.utils import get_instance

__all__ = [
    "BasicRNNDecoderOutput", "AttentionRNNDecoderOutput",
    "BasicRNNDecoder", "AttentionRNNDecoder"
]

class BasicRNNDecoderOutput(
        collections.namedtuple("BasicRNNDecoderOutput",
                               ("rnn_output", "sample_id"))):
    """The outputs of basic RNN decoders that include both RNN results and
    sampled ids at each step.

    This is the same as :class:`tensorflow.contrib.seq2seq.BasicDecoderOutput`.

    Attributes:
        rnn_output: The outputs of RNN at each step. E.g., in
            :class:`~txtgen.modules.BasicRNNDecoder`, this
            is a Tensor of shape `[batch_size, max_time, vocab_size]` containing
            the logits at each step.
        sample_id: The sampled results at each step. E.g., in
            :class:`~txtgen.modules.BasicRNNDecoder`
            with default helpers (e.g.,
            :class:`~txtgen.modules.EmbeddingTrainingHelper`), this is a Tensor
            of shape `[batch_size, max_time]` containing the sampled token
            index at each step.
    """
    pass

#TODO(zhiting): complete the docstring
class AttentionRNNDecoderOutput(
        collections.namedtuple(
            "AttentionRNNDecoderOutput",
            ["rnn_output", "sample_id", "cell_output",
             "attention_scores", "attention_context"])):
    """The outputs of attention RNN decoders that additionally include attention
    results.

    Attributes:
        rnn_output: The outputs of RNN at each step. E.g., in
            :class:`~txtgen.modules.AttentionRNNDecoder`, this is a Tensor of
            shape `[batch_size, max_time, vocab_size]` containing the logits
            at each step.
        sample_id: The sampled results at each step. E.g., in
            :class:`~txtgen.modules.AttentionRNNDecoder` with default helpers
            (e.g., :class:`~txtgen.modules.EmbeddingTrainingHelper`), this
            is a Tensor of shape `[batch_size, max_time]` containing the sampled
            token index at each step.
        cell_output: The output states of RNN cell at each step. E.g., in
            :class:`~txtgen.modules.AttentionRNNDecoder`, this is a Tensor of
            shape `[batch_size, max_time, cell_output_size]`.
        attention_scores: TODO
        attention_context: TODO
    """
    pass


class BasicRNNDecoder(RNNDecoderBase):
    """Basic RNN decoder that performs sampling at each step.

    Args:
        cell (RNNCell, optional): An instance of `RNNCell`. If `None`
            (default), a cell is created as specified in
            :attr:`hparams["rnn_cell"]` (see
            :meth:`~txtgen.modules.BasicRNNDecoder.default_hparams`).
        embedding (optional): A `Variable` or a 2D Tensor (or array)
            of shape `[vocab_size, embedding_dim]` that contains the token
            embeddings.

            Ignore if :attr:`hparams["use_embedding"]` is `False`. Otherwise:

            - If a `Variable`, this is directly used in decoding.

            - If a Tensor or array, a new `Variable` of token embedding is
              created using it as initialization value.

            - If `None` (default), a new `Variable` is created as specified in
              :attr:`hparams["embedding"]`.

        vocab_size (int, optional): Vocabulary size. Required if
            :attr:`hparams["use_embedding"]` is `False` or :attr:`embedding` is
            not provided.
        hparams (dict, optional): Hyperparameters. If not specified, the default
            hyperparameter setting is used. See
            :meth:`~txtgen.modules.BasicRNNDecoder.default_hparams` for the
            structure and default values.
    """

    def __init__(self,
                 cell=None,
                 embedding=None,
                 vocab_size=None,
                 hparams=None):
        RNNDecoderBase.__init__(self, cell, embedding, vocab_size, hparams)

    @staticmethod
    def default_hparams():
        """Returns a dictionary of hyperparameters with default values.

        Returns:
            .. code-block:: python

                {
                    "rnn_cell": default_rnn_cell_hparams(),
                    "use_embedding": True,
                    "embedding": default_embedding_hparams(),
                    "helper_train": default_helper_train_hparams(),
                    "max_decoding_length_train": None,
                    "helper_infer": default_helper_infer_hparams(),
                    "max_decoding_length_infer": None,
                    "name": "basic_rnn_decoder"
                }

            Here:

            "rnn_cell" : dict
                A dictionary of RNN cell hyperparameters. Ignored if
                :attr:`cell` is given when constructing the decoder.

                The default value is defined in
                :meth:`~txtgen.core.layers.default_rnn_cell_hparams`.

            "use_embedding" : bool
                Whether token embedding is used.

            "embedding" : dict
                A dictionary of token embedding hyperparameters for
                embedding initialization.

                Ignored if :attr:`embedding` is given and is `Variable`
                when constructing the decoder.

                If :attr:`embedding` is given and is a Tensor or array, the
                "dim" and "initializer" specs of "embedding" are ignored.

                The default value is defined in
                :meth:`~txtgen.core.layers.default_embedding_hparams`.

            "helper_train" : dict
                A dictionary of :class:`Helper` hyperparameters. The
                helper is used in training phase.

                The default value is defined in
                :meth:`~txtgen.modules.default_helper_train_hparams`

            "max_decoding_length_train": int or None
                Maximum allowed number of decoding steps in training phase.

                The default value is `None`, which means decoding is
                performed until fully done, e.g., encountering the <EOS> token.

            "helper_infer": dict
                A dictionary of :class:`Helper` hyperparameters. The
                helper is used in inference phase.

                The default value is defined in
                :meth:`~txtgen.modules.default_helper_infer_hparams`

            "max_decoding_length_infer" : int or None
                Maximum allowed number of decoding steps in inference phase.

                The default value is `None`, which means decoding is
                performed until fully done, e.g., encountering the <EOS> token.

            "name" : str
                Name of the decoder.

                The default value is "basic_rnn_decoder".
        """
        hparams = RNNDecoderBase.default_hparams()
        hparams["name"] = "basic_rnn_decoder"
        return hparams

    def initialize(self, name=None):
        return self._helper.initialize() + (self._initial_state,)

    def step(self, time, inputs, state, name=None):
        cell_outputs, cell_state = self._cell(inputs, state)
        logits = tf.contrib.layers.fully_connected(
            inputs=cell_outputs, num_outputs=self._vocab_size)
        sample_ids = self._helper.sample(
            time=time, outputs=logits, state=cell_state)
        (finished, next_inputs, next_state) = self._helper.next_inputs(
            time=time,
            outputs=logits,
            state=cell_state,
            sample_ids=sample_ids)
        outputs = BasicRNNDecoderOutput(logits, sample_ids)
        #next_state should be cell_state directly,
        #according to function next_inouts
        return (outputs, next_state, next_inputs, finished)

    def finalize(self, outputs, final_state, sequence_lengths):
        return outputs, final_state

    @property
    def output_size(self):
        return BasicRNNDecoderOutput(
            rnn_output=self._vocab_size,
            sample_id=tensor_shape.TensorShape([]))

    @property
    def output_dtype(self):
        return BasicRNNDecoderOutput(
            rnn_output=dtypes.float32, sample_id=dtypes.int32)

#TODO(zhiting): complete the docstring
class AttentionRNNDecoder(RNNDecoderBase):
    """RNN decoder with attention mechanism.

    Common arguments are the same as in
    :class:`~txtgen.modules.BasicRNNDecoder`, such as
    :attr:`cell`, :attr:`embedding`, and :attr:`vocab_size`.

    Args:
        attention_keys (): TODO
        attention_values (): TODO
        attention_value_length (): TODO

        cell_input_fn (callable, optional): A callable that produces RNN cell
            inputs. If `None` (default), the default is used:
            `lambda inputs, attention: tf.concat([inputs, attention], -1)`,
            which cancats regular RNN cell inputs with attentions.
        cell (RNNCell, optional): An instance of `RNNCell`. If `None`
            (default), a cell is created as specified in
            :attr:`hparams["rnn_cell"]` (see
            :meth:`~txtgen.modules.AttentionRNNDecoder.default_hparams`).
        embedding (optional): A `Variable` or a 2D Tensor (or array)
            of shape `[vocab_size, embedding_dim]` that contains the token
            embeddings.

            Ignore if :attr:`hparams["use_embedding"]` is `False`. Otherwise:

            - If a `Variable`, this is directly used in decoding.

            - If a Tensor or array, a new `Variable` of token embedding is
              created using it as initialization value.

            - If `None` (default), a new `Variable` is created as specified in
              :attr:`hparams["embedding"]`.

        vocab_size (int, optional): Vocabulary size. Required if
            :attr:`hparams["use_embedding"]` is `False` or :attr:`embedding` is
            not provided.
        hparams (dict, optional): Hyperparameters. If not specified, the default
            hyperparameter setting is used. See
            :meth:`~txtgen.modules.AttentionRNNDecoder.default_hparams` for the
            structure and default values.

    """
    def __init__(self,
                 n_hidden,  #TODO(zhiting): Is this typically inferred
                            # automatically, or manullay specified by users?
                            # If the latter, move this to hparams.
                 attention_keys, #TODO(zhiting): Please add docstring above
                 attention_values,
                 attention_values_length,
                 reverse_scores_lengths=None, #TODO(zhiting): this is not used?
                 cell_input_fn=None,
                 cell=None,
                 embedding=None,
                 vocab_size=None,
                 hparams=None):
        RNNDecoderBase.__init__(self, cell, embedding, vocab_size, hparams)

        #TODO(zhiting)
        att_params = hparams['attention']
        attention_class = hparams['attention']['class'] #LuongAttention
        attention_kwargs = hparams['attention']['params']
        attention_kwargs['num_units'] = n_hidden
        attention_kwargs['memory_sequence_length'] = attention_values_length
        attention_kwargs['memory'] = attention_keys
        attention_modules = ['txtgen.custom', 'tensorflow.contrib.seq2seq']
        attention_mechanism = get_instance(attention_class, attention_kwargs, attention_modules)

        wrapper_params = hparams['attention']['wrapper_params']
        attn_cell = AttentionWrapper(self._cell, attention_mechanism, **wrapper_params)
        self._cell = attn_cell

    @staticmethod
    def default_hparams():
        """Returns a dictionary of hyperparameters with default values:

        Common hyperparameters are the same as in
        :class:`~txtgen.modules.BasicRNNDecoder`
        (see :meth:`txtgen.modules.BasicRNNDecoder.default_hparams`).
        Additional hyperparameters are included for attention mechanism
        configuration.

        Returns:
            .. code-block:: python

                {
                    "attention": {
                        "type": "LuongAttention",
                        "kwargs": {
                            "num_units": 512,
                            "probability_fn": "tensorflow.nn.softmax"
                        },
                        "attention_layer_size": None,
                        "alignment_history": False,
                        "output_attention": True,
                    },
                    "rnn_cell": default_rnn_cell_hparams(),
                    "use_embedding": True,
                    "embedding": default_embedding_hparams(),
                    "helper_train": default_helper_train_hparams(),
                    "max_decoding_length_train": None,
                    "helper_infer": default_helper_infer_hparams(),
                    "max_decoding_length_infer": None,
                    "name": "attention_rnn_decoder"
                }

            Here:

            "attention" : dict
                A dictionary of attention hyperparameters, which includes:

                "type" : str
                    Name or full path to the attention class which can be

                    - Built-in attentions defined in \
                `tensorflow.contrib.seq2seq`, including \
                :class:`~tensorflow.contrib.seq2seq.LuongAttention`,\
                :class:`~tensorflow.contrib.seq2seq.BahdanauAttention`,\
                :class:`~tensorflow.contrib.seq2seq.BahdanauMonotonicAttention`\
                and \
                :class:`~tensorflow.contrib.seq2seq.LuongMonotonicAttention`.
                    - User-defined attention classes in `txtgen.custom`.
                    - External attention classes. Must provide the full path, \
                      e.g., "my_module.MyAttentionClass".

                    The default value is "LuongAttention".

                "kwargs" : dict
                    A dictionary of arguments for constructor of the attention
                    class.

        """
        hparams = RNNDecoderBase.default_hparams()
        hparams["name"] = "attention_rnn_decoder"
        hparams["attention"] = {
            "type": "LuongAttention",
            "kwargs": {
                "num_units": 512,
                "probability_fn": "tensorflow.nn.softmax"
            },
            "attention_layer_size": None,
            "alignment_history": False,
            "output_attention": True,
        }
        return hparams
    def initialize(self, name=None):
        helper_init = self._helper.initialize()
        return [helper_init[0], helper_init[1], self._initial_state]

    def step(self, time, inputs, state, name=None):
        cell_outputs, cell_state = self._cell(inputs, state)
        wrapper_outputs, wrapper_state = self._cell(inputs, state)

        #cell_state is AttentionWrapperState
        cell_state = wrapper_state.cell_state
        attention_scores = wrapper_state.alignments
        attention_context = wrapper_state.attention

        logits = tf.contrib.layers.fully_connected(
            inputs=cell_outputs, num_outputs=self._vocab_size)
        sample_ids = self._helper.sample(
            time=time, outputs=logits, state=cell_state)
        (finished, next_inputs, next_state) = self._helper.next_inputs(
            time=time,
            outputs=logits,
            state=wrapper_state,
            sample_ids=sample_ids)
        # there should be some problem
        outputs = AttentionRNNDecoderOutput(
            logits, sample_ids, wrapper_outputs,
            attention_scores, attention_context)
        return (outputs, next_state, next_inputs, finished)

    def finalize(self, outputs, final_state, sequence_lengths):
        return outputs, final_state


    @property
    def output_size(self):
        statesize = self.cell.state_size
        return AttentionRNNDecoderOutput(
            rnn_output=self._vocab_size,
            sample_id=tensor_shape.TensorShape([]),
            cell_output=self.cell._cell.output_size,
            attention_scores=statesize.alignments,
            attention_context=statesize.attention)

    @property
    def output_dtype(self):
        return AttentionRNNDecoderOutput(
            logits=dtypes.float32,
            predicted_ids=dtypes.int32,
            cell_output=dtypes.float32,
            attention_scores=dtypes.float32,
            attention_context=dtypes.float32)
