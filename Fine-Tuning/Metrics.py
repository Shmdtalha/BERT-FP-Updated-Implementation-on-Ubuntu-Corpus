import numpy as np
np.random.seed(0)
#This code based on https://github.com/chunyuanY/Dialogue metric

class Metrics(object):

    def __init__(self, score_file_path:str):
        super(Metrics, self).__init__()
        self.score_file_path = score_file_path
        self.segment = 10 #It depend on positive negative ratio 1:1 or 1:10

    def __read_socre_file(self, score_file_path):
        sessions = []
        one_sess = []
        with open(score_file_path, 'r') as infile:
            i = 0
            for line in infile.readlines():
                i += 1
                tokens = line.strip().split('\t')
                one_sess.append((float(tokens[0]), int(tokens[1])))
                if i % self.segment == 0:
                    one_sess_tmp = np.array(one_sess)
                    if one_sess_tmp[:, 1].sum() > 0:
                        sessions.append(one_sess)
                    one_sess = []
        return sessions


    def __mean_average_precision(self, sort_data):
        #to do
        count_1 = 0
        sum_precision = 0
        for index in range(len(sort_data)):
            if sort_data[index][1] == 1:
                count_1 += 1
                sum_precision += 1.0 * count_1 / (index+1)
        return sum_precision / count_1


    def __mean_reciprocal_rank(self, sort_data):
        sort_lable = [s_d[1] for s_d in sort_data]
        assert 1 in sort_lable
        return 1.0 / (1 + sort_lable.index(1))

    def __precision_at_position_1(self, sort_data):
        if sort_data[0][1] == 1:
            return 1
        else:
            return 0

    def __recall_at_position_k_in_10(self, sort_data, k):
        sort_label = [s_d[1] for s_d in sort_data]
        select_label = sort_label[:k]
        return 1.0 * select_label.count(1) / sort_label.count(1)


    def evaluation_one_session(self, data):
        
        np.random.shuffle(data)
        sort_data = sorted(data, key=lambda x: x[0], reverse=True)
        m_a_p = self.__mean_average_precision(sort_data)
        m_r_r = self.__mean_reciprocal_rank(sort_data)
        p_1   = self.__precision_at_position_1(sort_data)
        r_1   = self.__recall_at_position_k_in_10(sort_data, 1)
        r_2   = self.__recall_at_position_k_in_10(sort_data, 2)
        r_5   = self.__recall_at_position_k_in_10(sort_data, 5)
        return m_a_p, m_r_r, p_1, r_1, r_2, r_5


    def evaluate_all_metrics(self):
        sum_m_a_p = 0
        sum_m_r_r = 0
        sum_p_1 = 0
        sum_r_1 = 0
        sum_r_2 = 0
        sum_r_5 = 0

        sessions = self.__read_socre_file(self.score_file_path)
        total_s = len(sessions)
        for session in sessions:
            m_a_p, m_r_r, p_1, r_1, r_2, r_5 = self.evaluation_one_session(session)
            sum_m_a_p += m_a_p
            sum_m_r_r += m_r_r
            sum_p_1 += p_1
            sum_r_1 += r_1
            sum_r_2 += r_2
            sum_r_5 += r_5

        return (sum_m_a_p/total_s,
                sum_m_r_r/total_s,
                  sum_p_1/total_s,
                  sum_r_1/total_s,
                  sum_r_2/total_s,
                  sum_r_5/total_s)


if __name__ == '__main__':
    metric = Metrics('ubuntu_score_file0.txt')
    result = metric.evaluate_all_metrics()
    for r in result:
        print(r)



'''
    def rouge():
    import numpy as np
    import re
    from rouge import Rouge
    from nltk.tree import *
    from nltk.parse import CoreNLPParser
    from nltk.tokenize import sent_tokenize
    import tensorflow as tf
    import nltk
    import collections
    import math
    from glob import glob
    from tensorflow.python.tools.inspect_checkpoint import print_tensors_in_checkpoint_file
    
    def print_args(flags):
        """Print arguments."""
        print("\nParameters:")
        for attr in flags:
            value = flags[attr].value
            print("{}={}".format(attr, value))
        print("")
    
    
    def load_embedding(embed_file, vocab):
        emb_dict = dict()
        emb_size = tf.flags.FLAGS.embedding_dim
        with open(embed_file, 'r', encoding='utf8') as f:
            for line in f:
                tokens = line.strip().split(" ")
                word = tokens[0]
                vec = list(map(float, tokens[1:]))
                emb_dict[word] = vec
                if emb_size:
                    assert emb_size == len(vec), "All embedding size should be same."
                else:
                    emb_size = len(vec)
        oov_counter = 0
        for token in vocab:
            if token not in emb_dict:
                emb_dict[token] = [0.0] * emb_size
                oov_counter +=1
        print('oove:', oov_counter, 'total dic:', len(emb_dict))
        with tf.device('/cpu:0'), tf.compat.v1.name_scope("embedding"):
        #with tf.variable_scope("pretrain_embeddings", dtype=dtype):
            emb_table = np.array([emb_dict[token] for token in vocab], dtype=np.float32)
            emb_table = tf.convert_to_tensor(value=emb_table, dtype=tf.float32)
            print('---- emb_table:', emb_table)
    
        return emb_dict, emb_size, emb_table
    
    def clean_str(string):
        string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
        string = re.sub(r"\'s", " \'s", string)
        string = re.sub(r"\'ve", " \'ve", string)
        string = re.sub(r"n\'t", " n\'t", string)
        string = re.sub(r"\'re", " \'re", string)
        string = re.sub(r"\'d", " \'d", string)
        string = re.sub(r"\'ll", " \'ll", string)
        string = re.sub(r",", " , ", string)
        string = re.sub(r"!", " ! ", string)
        string = re.sub(r"\(", " \( ", string)
        string = re.sub(r"\)", " \) ", string)
        string = re.sub(r"\?", " \? ", string)
        string = re.sub(r"\s{2,}", " ", string)
        return string.strip().lower()
    
    
    
    def load_vocab(vocab_file):
        """load vocab from vocab file.
        Args:
            vocab_file: vocab file path
        Returns:
            vocab_table, vocab, vocab_size
        """
        
        vocab_table = tf.python.ops.lookup_ops.index_table_from_file( # Returns a lookup table that converts a string tensor into int64 IDs.
            vocabulary_file=vocab_file, default_value=0)
        vocab = []
        with open(vocab_file, "rb") as f:
            vocab_size = 0
            for word in f:
                vocab_size += 1
                vocab.append(word.strip())
        return vocab_table, vocab, vocab_size
    
    
    
    def load_model(sess, ckpt):
        with sess.as_default(): 
            with sess.graph.as_default(): 
                init_ops = [tf.compat.v1.global_variables_initializer(),
                            tf.compat.v1.local_variables_initializer(), tf.compat.v1.tables_initializer()]
                sess.run(init_ops)
                ckpt_path = tf.train.latest_checkpoint(ckpt)
                print("Loading saved model: " + ckpt_path)
                saver = tf.compat.v1.train.Saver()
                saver.restore(sess, ckpt_path)
    
    # The code for batch iterator:
    def _parse_infer_csv(line):
        cols_types = [['']] * 3
        columns = tf.io.decode_csv(records=line, record_defaults=cols_types, field_delim='\t')
        return columns
    
    def _parse_infer_test_csv(line):
        cols_types = [['']] * 2
        columns = tf.io.decode_csv(records=line, record_defaults=cols_types, field_delim='\t')
        return columns
    
    def _truncate(tensor):
        dim = tf.size(input=t)
        return tf.cond( pred=tf.greater(dim, k), true_fn=lambda: tf.slice(t, [0], [k]))
    
    def _split_string(tensor):
        results = np.array(re.split('\[|\]|, |,', tensor.decode("utf-8") ))
        results = [float(result) for result in results if result!='']
        return np.array(results).astype(np.float32)
    
    
    
    def get_iterator(data_file, vocab_table, batch_size, max_seq_len, padding=True,):
        """Iterator for train and eval.
        Args:
            data_file: data file, each line contains a sentence that must be ranked
            vocab_table: tf look-up table
            max_seq_len: sentence max length
            padding: Bool
                set True for cnn or attention based model to pad all samples into same length, must set seq_max_len
        Returns:
            (batch, size)
        """
        # interleave is very important to process multiple files at the same time
        dataset = tf.data.TextLineDataset(data_file) # reads the file with each line correspoding to one sample
        dataset = dataset.map(_parse_infer_csv)
        dataset = dataset.map(lambda score, sent, feats: (tf.strings.to_number(score, tf.float32), tf.compat.v1.string_split([sent]).values,\
                              tf.compat.v1.py_func(_split_string, inp=[feats], Tout=tf.float32)))
        #                        tf.string_split([feats], delimiter=',] ' ).values)) # you can set num_parallel_calls 
        dataset = dataset.map(lambda score, sent_tokens, feats: (score, tf.cond(pred=tf.greater(tf.size(input=sent_tokens),tf.flags.FLAGS.max_seq_len), 
                                                                         true_fn=lambda: tf.slice(sent_tokens, [0], [tf.flags.FLAGS.max_seq_len]), 
                                                                         false_fn=lambda: sent_tokens), feats)) # truncate to max_seq_length
        # Convert the word strings to ids.  Word strings that are not in the
        # vocab get the lookup table's default_value integer.
        dataset = dataset.map(lambda score, sent_tokens, feats:{'scores':score, 'tokens': tf.cast(vocab_table.lookup(sent_tokens), tf.int32), 'features': feats})
        if padding:
            batch_dataset = dataset.padded_batch(batch_size, padded_shapes={'scores':[],'tokens':[tf.flags.FLAGS.max_seq_len], 'features':[tf.flags.FLAGS.surf_features_dim]},
                                            padding_values=None,
                                            drop_remainder=False)
        else:
            batch_dataset = dataset.padded_batch(batch_size,padded_shapes={'scores':[],'tokens':[tf.flags.FLAGS.max_seq_len], 'features':[tf.flags.FLAGS.surf_features_dim]}, drop_remainder=False)
        batched_iter = tf.compat.v1.data.make_initializable_iterator(batch_dataset)
        next_batch = batched_iter.get_next()
    
        return batched_iter, next_batch
    
    '''
    '''
    def _pad_up_to(tensor):
        constant_values = 'None'
        s = tf.shape(tensor)
        paddings = [[0,tf.flags.FLAGS.max_seq_len - tensor.shape[0]]]  
        return tf.pad(tensor, paddings, 'CONSTANT', constant_values=constant_values)
    
    def get_dev_data(data_file, vocab_table, batch_size, max_seq_len, padding=True,):
        dataset = tf.data.TextLineDataset(data_file) # reads the file with each line correspoding to one sample
        dataset = dataset.map(_parse_infer_csv)
        dataset = dataset.map(lambda score, sent, feats: (tf.string_to_number(score, tf.float32), tf.string_split([sent]).values,\
                              tf.py_func(_split_string, inp=[feats], Tout=tf.float32)))
        dataset = dataset.map(lambda score, sent_tokens, feats: (score, tf.cond(tf.greater(tf.size(sent_tokens),tf.flags.FLAGS.max_seq_len), 
                                                                         lambda: tf.slice(sent_tokens, [0], [tf.flags.FLAGS.max_seq_len]), 
                                                                         lambda: sent_tokens), feats)) # truncate to max_seq_length
        dataset = dataset.map(lambda score, sent_tokens, feats:(score,tf.py_function(_pad_up_to, inp=[sent_tokens], Tout=tf.string),feats))
        dataset = dataset.map(lambda score, sent_tokens, feats:{'scores':score, 'tokens': tf.cast(vocab_table.lookup(sent_tokens), tf.int32), 'features': feats})
        iter = dataset.make_initializable_iterator()
        next_batch = iter.get_next()
        return iter, next_batch
    '''
    
    '''
    def get_test_iterator(data_file, 
                     vocab_table,
                     batch_size,
                     max_seq_len,
                     padding=True,):
    
        # interleave is very important to process multiple files at the same time
        dataset = tf.data.TextLineDataset(data_file) # reads the file with each line correspoding to one sample
        dataset = dataset.map(_parse_infer_test_csv)
        dataset = dataset.map(lambda  sent, feats: (tf.compat.v1.string_split([sent]).values,\
                              tf.compat.v1.py_func(_split_string, inp=[feats], Tout=tf.float32)))
        #                        tf.string_split([feats], delimiter=',] ' ).values)) # you can set num_parallel_calls 
        dataset = dataset.map(lambda sent_tokens, feats: ( tf.cond(pred=tf.greater(tf.size(input=sent_tokens),tf.flags.FLAGS.max_seq_len), 
                                                                         true_fn=lambda: tf.slice(sent_tokens, [0], [tf.flags.FLAGS.max_seq_len]), 
                                                                         false_fn=lambda: sent_tokens), feats)) # truncate to max_seq_length
        # Convert the word strings to ids.  Word strings that are not in the
        # vocab get the lookup table's default_value integer.
        dataset = dataset.map(lambda sent_tokens, feats:{'tokens': tf.cast(vocab_table.lookup(sent_tokens), tf.int32), 'features': feats})
        if padding:
            batch_dataset = dataset.padded_batch(batch_size, padded_shapes={'tokens':[tf.flags.FLAGS.max_seq_len], 'features':[tf.flags.FLAGS.surf_features_dim]},
                                            padding_values=None,
                                            drop_remainder=False)
        else:
            batch_dataset = dataset.padded_batch(batch_size,padded_shapes={'tokens':[tf.flags.FLAGS.max_seq_len], 'features':[tf.flags.FLAGS.surf_features_dim]}, drop_remainder=False)
        batched_iter = tf.compat.v1.data.make_initializable_iterator(batch_dataset)
        next_batch = batched_iter.get_next()
    
        return batched_iter, next_batch

'''




