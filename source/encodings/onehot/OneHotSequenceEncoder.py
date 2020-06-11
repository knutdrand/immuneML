
from source.data_model.dataset.SequenceDataset import SequenceDataset
from source.encodings.EncoderParams import EncoderParams
from source.encodings.onehot.OneHotEncoder import OneHotEncoder
from source.data_model.encoded_data.EncodedData import EncodedData



class OneHotSequenceEncoder(OneHotEncoder):
    """
    One-hot encoded repertoire data is represented in a matrix with dimensions:
        [sequences, sequence_lengths, one_hot_characters]

    when use_positional_info is true, the last 3 indices in one_hot_characters represents the positional information:
        - start position (high when close to start)
        - middle position (high in the middle of the sequence)
        - end position (high when close to end)
    """
    def _encode_new_dataset(self, dataset: SequenceDataset, params: EncoderParams):
        encoded_data = self._encode_data(dataset, params)

        encoded_dataset = SequenceDataset(filenames=dataset.get_filenames(),
                                          encoded_data=encoded_data,
                                          params=dataset.params,
                                          file_size=dataset.file_size)

        self.store(encoded_dataset, params)

        return encoded_dataset

    def _encode_data(self, dataset: SequenceDataset, params: EncoderParams):
        sequence_objs = [obj for obj in dataset.get_data(params["batch_size"])]

        sequences = [obj.get_sequence() for obj in sequence_objs]
        example_ids = dataset.get_example_ids()
        max_seq_len = max([len(seq) for seq in sequences])
        labels = self._get_labels(sequence_objs, params)

        examples = self._encode_sequence_list(sequences, pad_n_sequences=len(sequence_objs), pad_sequence_len=max_seq_len)

        encoded_data = EncodedData(examples=examples,
                                   labels=labels,
                                   example_ids=example_ids,
                                   encoding=OneHotEncoder.__name__)

        return encoded_data

    def _get_labels(self, sequence_objs, params: EncoderParams):
        label_names = params["label_configuration"].get_labels_by_name()
        labels = {name: [None] * len(sequence_objs) for name in label_names}

        for idx, sequence in enumerate(sequence_objs):
            for name in label_names:
                labels[name][idx] = sequence.get_attribute(name)

        return labels

