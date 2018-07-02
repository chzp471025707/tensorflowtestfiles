# filename:ts05.02.py # TensorFlow训练神经网络--全模型

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

# 1.设置输入和输出节点的个数,配置神经网络的参数
INPUT_NODE = 784  #输入层的节点数。对于MNIST数据集，这个就等于图片的像素
OUTPUT_NODE = 10  #输出层的节点数。这个等于类别的数目，因为MNIST数据集中需要区分0~9这十个数字，所以这里输出层的节点数为10.
LAYER1_NODE = 500 #隐藏层的节点数。这里使用只有一个隐藏层的网络作为样例，这个隐藏层有500个结点

BATCH_SIZE = 100  #一个训练batch中的训练数据个数。数字越小时，训练过程越接近随机梯度下降；数字越大，训练越接近梯度下降

# 模型相关的参数
LEARNING_RATE_BASE = 0.8     #基础的学习率
LEARNING_RATE_DECAY = 0.99   #学习率的衰减率
REGULARAZTION_RATE = 0.0001  #描述模型复杂度的正则化项在损失函数中的系数
TRAINING_STEPS = 5000        #训练的轮数
MOVING_AVERAGE_DECAY = 0.99  #滑动平均衰减率

#一个辅助函数，给定神经网络的输入和所有参数，计算神经网络的前向传播结果。在这里
#定义了一个使用ReLU激活函数的三层全连接神经网络。通过加入隐藏层实现了多层网络的结构
#通过ReLU激活函数实现了去线性化。在这个函数中也支持传入用于计算参数平均值的类，
#这样方便在测试时使用滑动平均模型
def inference(input_tensor, avg_class, weights1, biases1, weights2, biases2):
    # 当没有提供滑动平均类时，直接使用参数当前的取值
    if avg_class == None:
        # 计算隐藏层的前向传播结果
        #定义第一层隐藏层的计算结果
        layer1 = tf.nn.relu(tf.matmul(input_tensor, weights1) + biases1)
        # 计算输出层的前向传播结果。因为在计算损失时会一并计算softmax函数
        # 所以这里不需要加入激活函数。而且不加入softmax不影响预测结果。
        # 因为预测时使用的是不同类别对应结点输出值的不相对同大小，有没有softmax层
        # 对最后分类结果的计算没有影响。于是在计算整个神经网络的前向传播时可以
        # 不加入最后的softmax层。
        return tf.matmul(layer1, weights2) + biases2
    else:
        # 首先使用avg_class.average函数来计算得出变量的滑动平均值，
        # 然后在计算相应的神经网络前向传播结果
        layer1 = tf.nn.relu(tf.matmul(input_tensor, avg_class.average(weights1)) + avg_class.average(biases1))
        return tf.matmul(layer1, avg_class.average(weights2)) + avg_class.average(biases2)

# 3. 定义训练模型的过程
def train(mnist):
    x = tf.placeholder(tf.float32, [None, INPUT_NODE], name='x-input')
    y_ = tf.placeholder(tf.float32, [None, OUTPUT_NODE], name='y-input')
    # 生成隐藏层的参数。
    #生成一个矩阵，由输入节点数与隐藏层组成
    weights1 = tf.Variable(tf.truncated_normal([INPUT_NODE, LAYER1_NODE], stddev=0.1))
    biases1 = tf.Variable(tf.constant(0.1, shape=[LAYER1_NODE]))
    # 生成输出层的参数。
    weights2 = tf.Variable(tf.truncated_normal([LAYER1_NODE, OUTPUT_NODE], stddev=0.1))
    #biases2的权值为0.1，规模和输出节点一样
    biases2 = tf.Variable(tf.constant(0.1, shape=[OUTPUT_NODE]))

    # 计算在当前参数下神经网络前向传播的结果，这里给出的用于计算滑动平均的类为None,所以函数不会使用参数的滑动平均值
    y = inference(x, None, weights1, biases1, weights2, biases2)

    # 定义存储训练轮数的变量。这个变量不需要计算滑动平均值，所以这里指定这个变量为不可训练的变量（trainable=False）
    # Tensorflow训练神经网络时，一般会将代表训轮数的变量指定为不可训练的参数。

    # 将代表训练轮数的变量为不可变的参数
    global_step = tf.Variable(0, trainable=False)
    # 给定滑动_平均衰减率_和_训练轮数_的变量，初始化滑动平均类（见第4章）
    # 给定训练轮数的变量可以训练早期变量的更新速度
    variable_averages = tf.train.ExponentialMovingAverage(MOVING_AVERAGE_DECAY, global_step)
    # 在所有代表神经网络参数的变量上使用滑动平均，其他辅助变量就不需要了。tf.trainable.variable返回的就是图上集合
    variables_averages_op = variable_averages.apply(tf.trainable_variables())
    # 计算使用滑动平均之后前向传播的结果。滑动平均不会改变变量本身的取值，而会维护一个影子变量来记录
    # 其滑动平均值。所以当需要使用这个滑动平均值时，需要明确调用average（）函数。
    average_y = inference(x, variable_averages, weights1, biases1, weights2, biases2)

    # 计算交叉熵作为刻画预测值和真实值之间差距的损失函数，这里使用Tensorflow中提供的
    # sparse_softmax_cross_entropy_with_logits函数来计算交叉熵。当分类问题只有一个正确答案时，
    # 可以使用这个函数来加速交叉熵的计算。MNIST问题的图片中只包含了0~9中的一个数字，所以可以
    # 使用这一个函数来计算交叉损失。这个函数的第一个参数是神经网络不包括softmax的前向传播结果
    # 第二个是训练数据的正确答案。因为标准答案是一个长度为10的一维数组，而该函数需要提供的是
    # 一个正确答案的数字，所以需要使用tf.argmax(y_,1)函数来得到正确答案的编号
    cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=y, labels=tf.argmax(y_, 1))
    # 计算在当前batch中所有样例的交叉熵平均值。
    cross_entropy_mean = tf.reduce_mean(cross_entropy)

    # 定义计算L2正则化损失函数，REGULARIZATION_RATE表示模型复杂损失在总损失中的比例
    # 正则化的思想，在损失函数中加入刻画模型复杂程度的指标
    regularizer = tf.contrib.layers.l2_regularizer(REGULARAZTION_RATE)
    # 计算模型的正则化损失一般只计算神经网路权上的正则化损失，而不需要计算偏置顶
    regularaztion = regularizer(weights1) + regularizer(weights2)
    # 总损失等于交叉熵损失和正则化损失之和
    loss = cross_entropy_mean + regularaztion

    # 设置指数衰减的学习率。
    learning_rate = tf.train.exponential_decay(
        LEARNING_RATE_BASE,  #基础的学习率，随着迭代的进行，更新变量时使用的学习率在这个基础上递减
        global_step,         #当前迭代的轮数
        mnist.train.num_examples / BATCH_SIZE, #过完所有训练数据需要迭代的次数
        LEARNING_RATE_DECAY,  #学习率的衰减速度
        staircase=True)

    # 使用tf.train.GradientDescentOptimizer()函数优化算法来优化损失函数。
    # 这里的损失函数包含了交叉熵损失和L2正则化损失
    train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss, global_step=global_step)

    # 在训练神经网络模型时，每过一遍数据既需要通过反向传播来更新神经网络中的参数，
    # 又要更新每一个参数的滑动平均值。为了一次完成多个操作，Tensorflow提供了
    # tf.control_dependencies和tf.group两种机制，下面两行代码和
    # tf.control_dependencies([train_step,variable_averages_op])是等价的
    # tf.control_dependencies()控制计算流图的，给图中的某些计算指定顺序
    with tf.control_dependencies([train_step, variables_averages_op]):
        train_op = tf.no_op(name='train')

    # 检测使用了滑动平均模型的神经网络前向传播是否正确。tf.argmax(average_y,1)
    # 计算每一个样例的预测答案。其中average_y是一个batch_size*10的二维数组，
    # 每一行表示案例向前传播的结果。tf.argmax的第二个参数为1，表示选取最大值的
    # 操作只在第一个维度上进行（x轴上）,也就是说只在每一行选取最大值对应的下标
    # 于是得到的结果是一个长度为batch的一维数组，这个一维数组中的值就表示了每
    # 一个数字对应的样例识别的结果.tf.equal()判断每个Tensor的每一维度是否相同
    # 如果相等返回True，否则返回False.
    # axis = 0 的时候返回每一列最大值的位置索引，=1表示返回每一行最大值的位置索引
    correct_prediction = tf.equal(tf.argmax(average_y, 1), tf.argmax(y_, 1))
    # 这个运算首先将一个布尔型的值转换为实数型，然后计算平均值。
    # 这一个平均值就代表模型在这一组数据上的正确率
    #cast函数把第一个参数的值转换为第二个参数类型
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    # 初始化回话并开始训练过程。
    with tf.Session() as sess:
        tf.global_variables_initializer().run()
        # 准备验证数据。一般在神经网络的训练过程中会通过验证数据
        # 大致判断停止的条件和训练的结果
        validate_feed = {x: mnist.validation.images, y_: mnist.validation.labels}
        # 准备测试数据。在真实应用中，这部分数据在训练时是不可见的，这部分数据只是作为
        # 模型优劣的最后评价标准
        test_feed = {x: mnist.test.images, y_: mnist.test.labels}

        # 迭代训练神经网络
        for i in range(TRAINING_STEPS):
            # 每1000轮输出一次在训练集上的测试结果
            if i % 1000 == 0:
                # 计算滑动平均模型在验证数据上的结果。我也MNIST数据集比较小，所以一次
                # 可以处理所有的验证数据。为了计算方便。本程序没有将数据划分为更小的batch.
                # 当神经网络模型比价复杂或者验证数据比较大时，太大的batch会导致计算时间过长
                # 甚至导致内容溢出的错误
                validate_acc = sess.run(accuracy, feed_dict=validate_feed)
                print("After %d training step(s), validation accuracy using average model is %g " % (i, validate_acc))
            # 产生这一轮使用的一个batch训练集，并运行训练过程
            xs, ys = mnist.train.next_batch(BATCH_SIZE)
            sess.run(train_op, feed_dict={x: xs, y_: ys})
        # 训练结束之后，在测试数据上检验神经网络模型的最终正确率
        test_acc = sess.run(accuracy, feed_dict=test_feed)
        print(("After %d training step(s), test accuracy using average model is %g" % (TRAINING_STEPS, test_acc)))


# 4. 主程序入口，这里设定模型训练次数为5000次。
def main(argv=None):
    # 声明处理MNIST数据集的类，这个类在初始化数据时会自动下载数据
    mnist = input_data.read_data_sets("../../../datasets/MNIST_data", one_hot=True)
    train(mnist)

#Tensorflow提供一个主程序入口。tf.app.run()会调用上面定义的main函数
if __name__=='__main__':
    # 这句话的意思就是，当模块被直接运行时，以下代码块将被运行，当模块是被导入时，代码块不被运行。
    # tf.app.run()
    main()