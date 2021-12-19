from __future__ import division, print_function, absolute_import
import importlib.machinery
import tensorflow.keras.callbacks as tfcallbacks 
import utils.argmanager as argmanager
import utils.losses as losses
import utils.callbacks as callbacks
import data_generators.initializers as initializers
import pandas as pd
import os
import json

NARROWPEAK_SCHEMA = ["chr", "start", "end", "1", "2", "3", "4", "5", "6", "summit"]
os.environ['PYTHONHASHSEED'] = '0'

def get_model(args, parameters):
    # read model from file - can read model from pre-trained too - but not needed now - will add later
    architecture_module=importlib.machinery.SourceFileLoader('',args.architecture_from_file).load_module()
    model=architecture_module.getModelGivenModelOptionsAndWeightInits(args, parameters)
    print("got the model")
    model.summary()
    return model, architecture_module

def fit_and_evaluate(model,train_gen,valid_gen,args,architecture_module):
    model_output_path_string = args.output_prefix
    model_output_path_h5_name=model_output_path_string+".h5"
    model_output_path_logs_name=model_output_path_string+".log"
    model_output_path_arch_name=model_output_path_string+".arch"
    model_output_path_weights_name=model_output_path_string+".weights"

    checkpointer = tfcallbacks.ModelCheckpoint(filepath=model_output_path_h5_name, monitor="val_loss", mode="min",  verbose=1, save_best_only=True)
    earlystopper = tfcallbacks.EarlyStopping(monitor='val_loss', mode="min", patience=args.early_stop, verbose=1, restore_best_weights=True)
    history= callbacks.LossHistory(model_output_path_logs_name+".batch",args.trackables)
    csvlogger = tfcallbacks.CSVLogger(model_output_path_logs_name, append=False)
    reduce_lr = tfcallbacks.ReduceLROnPlateau(monitor='val_loss',factor=0.4, patience=args.early_stop-2, min_lr=0.00000001)
    cur_callbacks=[checkpointer,earlystopper,csvlogger,reduce_lr,history]
    #cur_callbacks=[checkpointer,earlystopper]

    model.fit(train_gen,
              validation_data=valid_gen,
              epochs=args.epochs,
              steps_per_epoch=10,
              verbose=1,
              max_queue_size=100,
              workers=10,
              callbacks=cur_callbacks)

    print('fit_generator complete') 
    print('save model') 
    model.save(model_output_path_h5_name)

    architecture_module.save_model_without_bias(model, model_output_path_string)


def get_model_param_dict(args):
    '''
    param_file has 2 columns -- param name in column 1, and param value in column 2
    You can pass model specfic parameters to design your own model with this
    '''
    params={}
    for line in open(args.params,'r').read().strip().split('\n'):
        tokens=line.split('\t')
        params[tokens[0]]=tokens[1]

    assert("counts_loss_weight" in params.keys()) # misising counts loss weight to use
    assert("filters" in params.keys()) # filters to use for the model not provided
    assert("n_dil_layers" in params.keys()) # n_dil_layers to use for the model not provided
    assert("inputlen" in params.keys()) # inputlen to use for the model not provided
    assert("outputlen" in params.keys()) # outputlen to use for the model not provided
    assert(args.chr_fold_path==params["chr_fold_path"]) # the parameters were generated on a different fold compared to the given fold
    assert(args.max_jitter==int(params["max_jitter"])) # the parameters were generated on a different jitter compared to the given jitter

    return params 

def main():

    # read arguments
    args=argmanager.fetch_train_chrombpnet_args()

    # read tab-seperated paprmeters file
    parameters = get_model_param_dict(args)
    print(parameters)

    # get model architecture to load
    model, architecture_module=get_model(args, parameters)

    # initialize generators to load data
    train_generator = initializers.initialize_generators(args, "train", parameters, return_coords=False)
    valid_generator = initializers.initialize_generators(args, "valid", parameters, return_coords=False)

    # train the model using the generators
    fit_and_evaluate(model, train_generator, valid_generator, args, architecture_module)

    # store args and and store params to checkpoint
    with open(args.output_prefix+'.args.json', 'w') as fp:
        json.dump(args.__dict__, fp,  indent=4)
    with open(args.output_prefix+'.params.json', 'w') as fp:
        json.dump(parameters, fp,  indent=4)


if __name__=="__main__":
    main()
