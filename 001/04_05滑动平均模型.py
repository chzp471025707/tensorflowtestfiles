# 在采用随机梯度下降法训练神经网络模型时，滑动平均模型能够提高训练模型在测试数据上面的效果

import tensorflow as tf

# 1. 定义一个变量用于计算滑动平均，这个变量的初始值为0.注意这里手动指定了变量
#的类型为tf.float32，因为所有需要计算滑动平均的变量必须是实数型
v1 = tf.Variable(0, dtype=tf.float32)
#这里step变量模拟神经网络迭代的轮数，可以用于动态控制衰减率
step = tf.Variable(0, trainable=False)
#定义一个滑动平均类初始化时给定衰减率（0.99）和控制衰减率的变量step
ema = tf.train.ExponentialMovingAverage(0.99, step)
#定义一个更新变量滑动平均的操作。这里需要给定一个列表，每次执行这个操作时
#这个列表中的变量都会被更新
maintain_averages_op = ema.apply([v1])

# 2. 查看不同迭代中变量取值的变化
with tf.Session() as sess:
    # 初始化所有变量
    init_op = tf.global_variables_initializer()
    sess.run(init_op)
    #通过ema.average(v1)获取滑动平均之后变量的取值。在初始化之后变量v1的值和v1的
    #滑动平均都为0
    print(sess.run([v1, ema.average(v1)])) #输出[0.0, 0.0]

    # 更新变量v1的取值到5
    sess.run(tf.assign(v1, 5))
    #更新v1的滑动平均值。衰减率为min[0.99,(1+step)/(10+step)= 0.1]=0.1,
    #所以v1的滑动平均会被更新为0.1 *0.1 + 0.9 * 5 = 4.5
    sess.run(maintain_averages_op)
    print(sess.run([v1, ema.average(v1)]))

    # 更新step和v1的取值为10000
    sess.run(tf.assign(step, 10000))
    #更新v1的值为10
    sess.run(tf.assign(v1, 10))
    #更新v1的滑动平均值。衰减率为min{0.99,(1+step)/(10+step)约等于0.999}=0.99,
    #所以v1的滑动平均会被更新为0.99 *4.5+ 0.01 * 10 = 4.555
    sess.run(maintain_averages_op)
    print(sess.run([v1, ema.average(v1)]))
    #输出[10.0, 4.5549988]

    # 再次更新滑动平均值，得到的新滑动平均值为0.99 *4.555 + 0.01 * 10 = 4.60945
    sess.run(maintain_averages_op)
    print(sess.run([v1, ema.average(v1)]))
    #输出[10.0, 4.6094499]
