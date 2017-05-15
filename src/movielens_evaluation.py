import tensorflow as tf
import numpy as np
import os
#from PhasedLSTMCell_v1 import *
#from PhasedLSTMCell import *
import time
import sys
import pickle
from rnn_dynamic import *
# from rnn_attentional import * #For the attentional experiment


checkpoint_path = 'checkpoints/rep0-lstm2-256-1-128-adam-10000000000-20170511-173749/best_model/model_best.ckpt-3072000'

max_interactions = 100

with open("pickles/movielens/X_test_" + str(max_interactions) + "_2009_filter20.pickle", 'rb') as handle:
    X_test = pickle.load(handle)
with open("pickles/movielens/Y_test_" + str(max_interactions) + "_2009_filter20.pickle", 'rb') as handle:
    Y_test = pickle.load(handle)


# tensorflow model
model_parameters = {}
model_parameters['opt'] = 'adam'
model_parameters['learning_rate'] = 0.01
model_parameters['n_hidden'] = 256
model_parameters['batch_size'] = 128
model_parameters['rnn_type'] = 'lstm2'
model_parameters['rnn_layers'] = 1
model_parameters['dropout'] = 0.0
model_parameters['l2_reg'] = 0.0
model_parameters['type_output'] = 'softmax'
model_parameters['max_steps'] = 3000000
model_parameters['padding'] = 'right'
model_parameters['n_input'] = X_test[0].toarray().shape[1]
model_parameters['n_output'] = Y_test[0].toarray().shape[1]
model_parameters['seq_length'] = X_test[0].toarray().shape[0]
model_parameters['embedding_size'] = 64
model_parameters['embedding_activation'] = 'linear'
model_parameters['y_length'] = 1
# Parameters for the attentional model only
model_parameters['attentional_layer'] = 'embedding'
model_parameters['init_stdev'] = 0.01



# Create tensorflow model and train
print('Create model...')
model = RNN_dynamic(model_parameters)
model.create_model()


def evaluate_sample(predictions, y_true, k):
    idx_predictions = np.arange(len(predictions))
    sorted_pred, sorted_idx = zip(*sorted(zip(predictions,idx_predictions), reverse=True))
    # Recall
    _, y_true_idx = np.where(y_true ==1)
    correct_idx = set(sorted_idx[:k]).intersection(set(y_true_idx))
    num_pos_k = len(correct_idx)
    total_pos = len(y_true)
    recall_user_k = (num_pos_k/float(total_pos))
    # Sps
    first_movie = y_true_idx[0]
    if first_movie in sorted_idx[0:k]:
        sps_k = 1
    else:
        sps_k = 0
    # Map
    sum_precisions = 0
    actual_pos = 0
    for i in range(k):
        if sorted_idx[i] in y_true_idx:
            actual_pos += 1 #CHECK THIS!! IT MAY BE NOT CORRECT
            sum_precisions += actual_pos/float(i+1)
    ap_k = sum_precisions/min(k, len(y_true))
    
    return recall_user_k, sps_k, ap_k, num_pos_k, total_pos

    
# Make predictions in chunks

k = 10
recalls = []
spss = []
aps = []
num_poss = []
total_poss = []

num_movies = Y_test[0].toarray().shape[1]
batch_size = 100
for i in range(0, len(X_test), batch_size):
    x_test = [x.toarray() for x in X_test[i:i+batch_size]]
    y_test = [y.toarray() for y in Y_test[i:i+batch_size]]
    logits, y_pred = model.predict(x_test, checkpoint_path)
    for j in range(len(y_pred)):
        recall_user_k, sps_k, ap_k, num_pos_k, total_pos = evaluate_sample(y_pred[j], y_test[j], k)
        recalls.append(recall_user_k)
        spss.append(sps_k)
        aps.append(ap_k)
        num_poss.append(num_pos_k)
        total_poss.append(total_pos)
    print(str(i) + '/' + str(len(X_test)))

print('Mean recall users: ' + str(np.mean(recalls)))
print('Mean spss: ' + str(np.mean(spss)))
print('MAP: ' + str(np.mean(aps)))
total_recall = np.sum(num_poss)/float(np.sum(total_poss))
print('Total Recall (no mean recall users): ' + str(total_recall))