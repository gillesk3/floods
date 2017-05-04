from resources.resource import nets
from resources.resource import tracker
from resources.resource import dataset
from resources.resource import preprocess
from resources.resource import image as satImage
import os,sys
import tensorflow as tf
import numpy as np
from PIL import Image
slim = tf.contrib.slim


netsList = {'incept':nets.inceptResV2}
scopeList ={'incept':nets.inceptResV2ArgScope}

#Not sure where weightDecay is used
def getNetFunc(name,numClasses,weightDecay=0.0,isTraining=False):


    if name not in netsList:
        raise ValueError('Network: %s not found' %name)

    func = netsList[name]

    def netFunc(images):
        argScope = scopeList[name](weightDecay=weightDecay)
        with slim.arg_scope(argScope):
            return func(images,numClasses,isTraining=isTraining)

    if hasattr(func,'defaultImageSize'):
        netFunc.defaultImageSize = func.defaultImageSize

    return netFunc

def displayImageTensor(imageTensor):
    tensor = np.squeeze(imageTensor,axis=(2,))
    im = Image.fromarray(tensor)
    # im.thumbnail(1000,1000)
    im.show()


networkName = 'incept'
isTraining = True

with tf.Graph().as_default():

    globalStep = slim.create_global_step()


    #Load dataset from tracker class
    stalker = tracker()

    network = getNetFunc(networkName,numClasses=stalker.numLabels(),isTraining=isTraining)

    fileQueue = dataset.getFileQueue()
    imagePath,image = dataset.readFile(fileQueue)
    image = preprocess.preprocessImage(image,netsList[networkName].defaultImageSize,netsList[networkName].defaultImageSize,isTraining=True)
    with tf.Session() as sesh:

        tf.global_variables_initializer().run()
        coords = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(coord=coords)

        imageTensor = sesh.run([image,imagePath])

        # for proc in psutil.process_iter():
        #     if proc.name() == "display":
        #         proc.kill()

        imageTensor = imageTensor[0]
        print(imageTensor)
        # imagePath = imageTensor[1].decode('utf-8')
        #
        # imageSat = satImage(imagePath)
        # displayImageTensor(imageTensor)
        coords.request_stop()
        coords.join(threads)






#     ######################
#     # Select the dataset #
#     ######################
#     dataset = dataset_factory.get_dataset(
#         FLAGS.dataset_name, FLAGS.dataset_split_name, FLAGS.dataset_dir)
#
#
#
#     #####################################
#     # Select the preprocessing function #
#     #####################################
#     preprocessing_name = FLAGS.preprocessing_name or FLAGS.model_name
#     image_preprocessing_fn = preprocessing_factory.get_preprocessing(
#         preprocessing_name,
#         is_training=True)
#
#     ##############################################################
#     # Create a dataset provider that loads data from the dataset #
#     ##############################################################
#     with tf.device(deploy_config.inputs_device()):
#       provider = slim.dataset_data_provider.DatasetDataProvider(
#           dataset,
#           num_readers=FLAGS.num_readers,
#           common_queue_capacity=20 * FLAGS.batch_size,
#           common_queue_min=10 * FLAGS.batch_size)
#       [image, label] = provider.get(['image', 'label'])
#       label -= FLAGS.labels_offset
#
#       train_image_size = FLAGS.train_image_size or network_fn.default_image_size
#
#       image = image_preprocessing_fn(image, train_image_size, train_image_size)
#
#       images, labels = tf.train.batch(
#           [image, label],
#           batch_size=FLAGS.batch_size,
#           num_threads=FLAGS.num_preprocessing_threads,
#           capacity=5 * FLAGS.batch_size)
#       labels = slim.one_hot_encoding(
#           labels, dataset.num_classes - FLAGS.labels_offset)
#       batch_queue = slim.prefetch_queue.prefetch_queue(
#           [images, labels], capacity=2 * deploy_config.num_clones)
#
#     ####################
#     # Define the model #
#     ####################
#     def clone_fn(batch_queue):
#       """Allows data parallelism by creating multiple clones of network_fn."""
#       images, labels = batch_queue.dequeue()
#       logits, end_points = network_fn(images)
#
#       #############################
#       # Specify the loss function #
#       #############################
#       if 'AuxLogits' in end_points:
#         tf.losses.softmax_cross_entropy(
#             logits=end_points['AuxLogits'], onehot_labels=labels,
#             label_smoothing=FLAGS.label_smoothing, weights=0.4, scope='aux_loss')
#       tf.losses.softmax_cross_entropy(
#           logits=logits, onehot_labels=labels,
#           label_smoothing=FLAGS.label_smoothing, weights=1.0)
#       return end_points
#
#     # Gather initial summaries.
#     summaries = set(tf.get_collection(tf.GraphKeys.SUMMARIES))
#
#     clones = model_deploy.create_clones(deploy_config, clone_fn, [batch_queue])
#     first_clone_scope = deploy_config.clone_scope(0)
#     # Gather update_ops from the first clone. These contain, for example,
#     # the updates for the batch_norm variables created by network_fn.
#     update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS, first_clone_scope)
#
#     # Add summaries for end_points.
#     end_points = clones[0].outputs
#     for end_point in end_points:
#       x = end_points[end_point]
#       summaries.add(tf.summary.histogram('activations/' + end_point, x))
#       summaries.add(tf.summary.scalar('sparsity/' + end_point,
#                                       tf.nn.zero_fraction(x)))
#
#     # Add summaries for losses.
#     for loss in tf.get_collection(tf.GraphKeys.LOSSES, first_clone_scope):
#       summaries.add(tf.summary.scalar('losses/%s' % loss.op.name, loss))
#
#     # Add summaries for variables.
#     for variable in slim.get_model_variables():
#       summaries.add(tf.summary.histogram(variable.op.name, variable))
#
#     #################################
#     # Configure the moving averages #
#     #################################
#     if FLAGS.moving_average_decay:
#       moving_average_variables = slim.get_model_variables()
#       variable_averages = tf.train.ExponentialMovingAverage(
#           FLAGS.moving_average_decay, global_step)
#     else:
#       moving_average_variables, variable_averages = None, None
#
#     #########################################
#     # Configure the optimization procedure. #
#     #########################################
#     with tf.device(deploy_config.optimizer_device()):
#       learning_rate = _configure_learning_rate(dataset.num_samples, global_step)
#       optimizer = _configure_optimizer(learning_rate)
#       summaries.add(tf.summary.scalar('learning_rate', learning_rate))
#
#     if FLAGS.sync_replicas:
#       # If sync_replicas is enabled, the averaging will be done in the chief
#       # queue runner.
#       optimizer = tf.train.SyncReplicasOptimizer(
#           opt=optimizer,
#           replicas_to_aggregate=FLAGS.replicas_to_aggregate,
#           variable_averages=variable_averages,
#           variables_to_average=moving_average_variables,
#           replica_id=tf.constant(FLAGS.task, tf.int32, shape=()),
#           total_num_replicas=FLAGS.worker_replicas)
#     elif FLAGS.moving_average_decay:
#       # Update ops executed locally by trainer.
#       update_ops.append(variable_averages.apply(moving_average_variables))
#
#     # Variables to train.
#     variables_to_train = _get_variables_to_train()
#
#     #  and returns a train_tensor and summary_op
#     total_loss, clones_gradients = model_deploy.optimize_clones(
#         clones,
#         optimizer,
#         var_list=variables_to_train)
#     # Add total_loss to summary.
#     summaries.add(tf.summary.scalar('total_loss', total_loss))
#
#     # Create gradient updates.
#     grad_updates = optimizer.apply_gradients(clones_gradients,
#                                              global_step=global_step)
#     update_ops.append(grad_updates)
#
#     update_op = tf.group(*update_ops)
#     train_tensor = control_flow_ops.with_dependencies([update_op], total_loss,
#                                                       name='train_op')
#
#     # Add the summaries from the first clone. These contain the summaries
#     # created by model_fn and either optimize_clones() or _gather_clone_loss().
#     summaries |= set(tf.get_collection(tf.GraphKeys.SUMMARIES,
#                                        first_clone_scope))
#
#     # Merge all summaries together.
#     summary_op = tf.summary.merge(list(summaries), name='summary_op')
#
#
#     ###########################
#     # Kicks off the training. #
#     ###########################
#     slim.learning.train(
#         train_tensor,
#         logdir=FLAGS.train_dir,
#         master=FLAGS.master,
#         is_chief=(FLAGS.task == 0),
#         init_fn=_get_init_fn(),
#         summary_op=summary_op,
#         number_of_steps=FLAGS.max_number_of_steps,
#         log_every_n_steps=FLAGS.log_every_n_steps,
#         save_summaries_secs=FLAGS.save_summaries_secs,
#         save_interval_secs=FLAGS.save_interval_secs,
#         sync_optimizer=optimizer if FLAGS.sync_replicas else None)
#
