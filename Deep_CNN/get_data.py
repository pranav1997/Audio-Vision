# -*- coding: utf-8 -*-
"""
author: @adityac8
"""
import csv
from keras_aud import aud_audio, aud_feature
from keras_aud import aud_model, aud_utils
import config as cfg
import numpy as np
import scipy
import cPickle

class GetValues:
    def __init__(self,**kwargs):
        self.kwargs=kwargs
    def get_parameters(self,**kwargs):
        self.prep=kwargs.get('prep','eval')               # dev or eval
        self.folds=kwargs.get('folds',4)                  # Number of folds
        self.save_model=kwargs.get('save_model',False)    # True if we want to save model
        self.model_type=kwargs.get('model_type','Functional') # Can be Dynamic or Functional
        self.model=kwargs.get('model','CNN')               # Name of model
        self.feature=kwargs.get('feature','logmel')        # Name of feature
        
        self.dropout=kwargs.get('dropout',0.1)             # 1st Dropout
        self.act1=kwargs.get('act1','relu')                # 1st Activation
        self.act2=kwargs.get('act2','relu')             # 2nd Activation
        self.act3=kwargs.get('act3','softmax')                # 3rd Activation
        self.nb_filter=kwargs.get('nb_filter',[128,256])             
        self.pool_size=kwargs.get('pool_size',[(3,3),(2,2)])

        self.input_neurons=kwargs.get('input_neurons',500) # Number of Neurons
        self.epochs=kwargs.get('epochs',10)                # Number of Epochs
        self.batchsize=kwargs.get('batchsize',100)         # Batch Size
        self.num_classes=kwargs.get('num_classes',15)      # Number of classes
        
        self.agg_num=kwargs.get('agg_num',10)              # Number of frames
        self.hop=kwargs.get('hop',10)                      # Hop Length
        self.loss=kwargs.get('loss','binary_crossentropy')
        self.optimizer=kwargs.get('optimizer','adam')
        self.dataset =kwargs.get('dataset', None)
        return self.prep, self.folds, self.save_model, self.model_type,\
               self.model,self.feature, self.dropout, self.act1, self.act2,\
               self.act3, self.input_neurons, self.epochs, self.batchsize,\
               self.num_classes, self.agg_num, self.hop, self.loss,\
               self.nb_filter, self.pool_size, self.optimizer, self.dataset

    def get_train_data(self):
        """
        Loads all the features saved as pickle files.
        Input: Features folder(str), CSV file(str)
        Output: Loaded features(np array) and labels(np array).
        """
        feature  = self.feature
        fe_fd    = cfg.dev_fd+'/'+feature
        csv_file = cfg.label_csv
        agg_num  = self.agg_num
        hop      = self.hop 
        # read csv
        with open( csv_file, 'rb') as f:
            reader = csv.reader(f)
            lis = list(reader)
        
        # init list
        X3d_all = []
        y_all = []
        i=0
        for li in lis:
            # load data
            [na, lb] = li[0].split('\t')
            na = na.split('/')[1][0:-4]
            path = fe_fd + '/' + na + '.f'
            X = aud_feature.load(path)
            # reshape data to (n_block, n_time, n_freq)
            i+=1
            X3d = aud_utils.mat_2d_to_3d( X, agg_num, hop )
            X3d_all.append( X3d )
            y_all += [ cfg.lb_to_id[lb] ] * len( X3d )
        
        print "Features loaded",i                
        print 'All files loaded successfully'
        # concatenate list to array
        X3d_all = np.concatenate( X3d_all )
        y_all = np.array( y_all )
        
        return X3d_all, y_all
    
    def get_test_predictions(self,md):
        model    = self.model
        feature  = self.feature
        fe_fd    = cfg.eva_fd+'/'+feature
        csv_file = cfg.txt_eva_path
        agg_num  = self.agg_num
        hop      = self.hop
        eva_file = cfg.eva_file
        # load name of wavs to be classified
        with open( csv_file, 'rb') as f:
            reader = csv.reader(f)
            lis = list(reader)
        
        # do classification for each file
        names = []
        pred_lbs = []
        
        for li in lis:
            names.append( li[0] )
            na = li[0][6:-4]
            #audio evaluation name
            fe_path = fe_fd + '/' + na + '.f'
            X0 = cPickle.load( open( fe_path, 'rb' ) )
            X0 = aud_utils.mat_2d_to_3d( X0, agg_num, hop)
            
            X0 = aud_utils.mat_3d_to_nd(model,X0)
        
            # predict
            p_y_preds = md.predict(X0)        # probability, size: (n_block,label)
            preds = np.argmax( p_y_preds, axis=-1 )     # size: (n_block)
            b = scipy.stats.mode(preds)
            pred = int( b[0] )
            pred_lbs.append( cfg.id_to_lb[ pred ] )
        
        pred = []    
        # write out result
        for i1 in xrange( len( names ) ):
            fname = names[i1] + '\t' + pred_lbs[i1] + '\n' 
            pred.append(fname)
            
        print 'write out finished!'
        truth = open(eva_file,'r').readlines()
        pred = [i.split('\t')[1].split('\n')[0]for i in pred]
        truth = [i.split('\t')[1]for i in truth]
        pred.sort()
        truth.sort()
        return truth,pred
