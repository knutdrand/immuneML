from collections import Counter

from source.data_model.dataset.SequenceDataset import SequenceDataset
from source.encodings.EncoderParams import EncoderParams
from source.encodings.kmer_frequency.KmerFrequencyEncoder import KmerFrequencyEncoder


class KmerFreqSequenceEncoder(KmerFrequencyEncoder):

    def _encode_new_dataset(self, dataset, params: EncoderParams):

        encoded_data = self._encode_data(dataset, params)

        encoded_dataset = SequenceDataset(filenames=dataset.get_filenames(),
                                          encoded_data=encoded_data,
                                          params=dataset.params)

        self.store(encoded_dataset, params)

        return encoded_dataset

    def _encode_examples(self, dataset, params: EncoderParams):

        encoded_sequences = []
        sequence_ids = []
        label_config = params["label_configuration"]
        labels = {label: [] for label in label_config.get_labels_by_name()}

        sequence_encoder = self._prepare_sequence_encoder(params)
        feature_names = sequence_encoder.get_feature_names(params)
        for sequence in dataset.get_data(params["batch_size"]):
            counts = self._encode_sequence(sequence, params, sequence_encoder, Counter())
            encoded_sequences.append(counts)
            sequence_ids.append(sequence.identifier)

            for label_name in label_config.get_labels_by_name():
                label = sequence.metadata.custom_params[label_name]
                labels[label_name].append(label)

        return encoded_sequences, sequence_ids, labels, feature_names