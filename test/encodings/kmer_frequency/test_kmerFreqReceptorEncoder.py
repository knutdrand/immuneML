import os
import pickle
import shutil
from unittest import TestCase

import numpy

from immuneML.analysis.data_manipulation.NormalizationType import NormalizationType
from immuneML.caching.CacheType import CacheType
from immuneML.data_model.dataset.ReceptorDataset import ReceptorDataset
from immuneML.data_model.receptor.TCABReceptor import TCABReceptor
from immuneML.data_model.receptor.receptor_sequence.ReceptorSequence import ReceptorSequence
from immuneML.encodings.EncoderParams import EncoderParams
from immuneML.encodings.kmer_frequency.KmerFreqReceptorEncoder import KmerFreqReceptorEncoder
from immuneML.encodings.kmer_frequency.ReadsType import ReadsType
from immuneML.encodings.kmer_frequency.sequence_encoding.SequenceEncodingType import SequenceEncodingType
from immuneML.environment.Constants import Constants
from immuneML.environment.EnvironmentSettings import EnvironmentSettings
from immuneML.environment.LabelConfiguration import LabelConfiguration
from immuneML.util.PathBuilder import PathBuilder


class TestKmerFreqReceptorEncoder(TestCase):

    def setUp(self) -> None:
        os.environ[Constants.CACHE_TYPE] = CacheType.TEST.name

    def test(self):

        receptors = [TCABReceptor(alpha=ReceptorSequence(amino_acid_sequence="AAACCC"), beta=ReceptorSequence(amino_acid_sequence="AAACCC"), identifier="1"),
                     TCABReceptor(alpha=ReceptorSequence(amino_acid_sequence="AAA"), beta=ReceptorSequence(amino_acid_sequence="CCC"), identifier="2"),
                     TCABReceptor(alpha=ReceptorSequence(amino_acid_sequence="AAACCC"), beta=ReceptorSequence(amino_acid_sequence="AAACCC"), identifier="3"),
                     TCABReceptor(alpha=ReceptorSequence(amino_acid_sequence="AAA"), beta=ReceptorSequence(amino_acid_sequence="CCC"), identifier="4")]

        path = EnvironmentSettings.tmp_test_path / "kmer_receptor_frequency/"
        PathBuilder.build(path)
        filename = path / "receptors.pkl"
        with open(filename, "wb") as file:
            pickle.dump(receptors, file)

        lc = LabelConfiguration()
        lc.add_label("l1", [1, 2])

        dataset = ReceptorDataset(labels={"l1": [1, 2]}, filenames=[filename], identifier="d1")

        encoder = KmerFreqReceptorEncoder.build_object(dataset, **{
                "normalization_type": NormalizationType.RELATIVE_FREQUENCY.name,
                "reads": ReadsType.UNIQUE.name,
                "sequence_encoding": SequenceEncodingType.CONTINUOUS_KMER.name,
                "k": 3
            })

        encoded_dataset = encoder.encode(dataset, EncoderParams(
            result_path=path / "2/",
            label_config=lc,
            pool_size=2,
            learn_model=True,
            model={},
            filename="dataset.csv",
            encode_labels=False
        ))

        self.assertEqual(4, encoded_dataset.encoded_data.examples.shape[0])
        self.assertTrue(all(identifier in encoded_dataset.encoded_data.example_ids
                            for identifier in ['1', '2', '3', '4']))
        self.assertTrue(numpy.array_equal(encoded_dataset.encoded_data.examples[0].A, encoded_dataset.encoded_data.examples[2].A))
        self.assertTrue(all(feature_name in encoded_dataset.encoded_data.feature_names for feature_name in ["alpha_AAA", "alpha_AAC", "beta_CCC"]))

        shutil.rmtree(path)
