import numpy as np
import pyglet


class ArmEnv(object):
	viewer = None
	dt = 0.1   #转动的速度和dt有关
	action_bound = [-1,1]    #转动的角度范围
	goal = {'x':100,'y':100,'l':40}   #物体的goal坐标和长度l
	state_dim = 9     #两个观测值
	action_dim = 2     #两个动作

	def __init__(self):
		self.arm_info = np.zeros(
			2,dtype = [('l',np.float32),('r',np.float32)])   #生成（2,2）的矩阵
		self.arm_info['l'] = 100   #两段手臂都长100
		self.arm_info['r'] = np.pi/6  #两段手臂的端点角度
		self.on_goal = 0   #判断手臂是否在目标上

	
	def step(self,action):
		done = False

		#计算单位时间dt内旋转的角度，将角度限制在360度以内
		action = np.clip(action,*self.action_bound)
		self.arm_info['r'] += action * self.dt
		self.arm_info['r'] %= np.pi * 2

		#如果手指接触到蓝色的goal，我们判定结束回合（done）
		#所以需要计算finger的坐标
		(a1l,a2l) = self.arm_info['l']
		(a1r,a2r) = self.arm_info['r']
		a1xy = np.array([200,200])   #a1 start(x0,y0)
		a1xy_ = np.array([np.cos(a1r),np.sin(a1r)]) * a1l + a1xy  #a1 end and a2 start(x1,y1)
		finger = np.array([np.cos(a1r + a2r),np.sin(a1r + a2r)]) * a2l + a1xy_   #a2end (x2,y2)

		dist1 = [(self.goal['x'] - a1xy_[0]) / 400, (self.goal['y'] - a1xy_[1]) / 400]
		#dist2是finger离goal的x,y方向的距离
		dist2 = [(self.goal['x'] - finger[0])/400,(self.goal['y'] - finger[1])/400]
		r = -np.sqrt(dist2[0]**2 + dist2[1]**2)

		#根据finger和goal的坐标得出done 和 reward
		if self.goal['x'] - self.goal['l']/2 < finger[0] < self.goal['x'] + self.goal['l']/2:
			if self.goal['y'] - self.goal['l']/2 < finger[1] < self.goal['y'] + self.goal['l']/2:
				self.on_goal += 1
				r += 1
				if self.on_goal > 50:
					done = True
		else:	
			self.on_goal = 0   #finger在goal以内
		#此时state有9个信息，分别会两截手臂端点到中心的x,y坐标（共8个），最后一个信息是finger是否在goal区域内
		s = np.concatenate((a1xy_/200, finger/200, dist1 + dist2, [1. if self.on_goal else 0.]))
		return s,r,done

	def reset(self):
		self.goal['x'] = np.random.rand()*400
		self.goal['y'] = np.random.rand()*400
		self.arm_info['r'] = 2 * np.pi * np.random.rand(2)
		self.on_goal = 0
		(a1l,a2l) = self.arm_info['l']
		(a1r,a2r) = self.arm_info['r']
		a1xy = np.array([200,200])
		a1xy_ = np.array([np.cos(a1r),np.sin(a1r)]) * a1l + a1xy
		finger = np.array([np.cos(a1r +a2r),np.sin(a1r + a2r)]) * a2l +a1xy_

		dist1 = [(self.goal['x'] - a1xy_[0])/400,(self.goal['y'] - a1xy_[1])/400]
		dist2 = [(self.goal['x'] - finger[0])/400,(self.goal['y'] - finger[1])/400]

		s = np.concatenate((a1xy_/200,finger/200,dist1 + dist2,[1. if self.on_goal else 0.]))

		return s

	def render(self):
		if self.viewer is None:   #如果调用了render，而且没有viewer,就生成一个
			self.viewer = Viewer(self.arm_info,self.goal)
		self.viewer.render()  #使用Viewer中的render功能

	def sample_action(self):
		return np.random.rand(2) - 0.5	

class Viewer(pyglet.window.Window):
	bar_thc = 5 #手臂的厚度


	def __init__(self,arm_info,goal):
    	#创建窗口的继承
    	#vsync如果是Ture，按屏幕频率刷新，反之不按此频率刷新
		super(Viewer,self).__init__(width = 400,height = 400,resizable = False,caption = 'Arm',vsync = False)

        #窗口背景颜色
		pyglet.gl.glClearColor(1,1,1,1)

		self.arm_info = arm_info
		self.goal_info = goal
		self.center_coord = np.array([200,200])   #添加窗口的中心点，手臂的根

        #将手臂的作图信息放入这个batch
		self.batch = pyglet.graphics.Batch()

		     #添加arm信息
		
		
		self.goal = self.batch.add(			#蓝色goal的信息包括x,y坐标，goal的长度l
			4,pyglet.gl.GL_QUADS,None,
			('v2f',[goal['x'] - goal['l']/2,goal['y'] - goal['l']/2,
				    goal['x'] - goal['l']/2,goal['y'] + goal['l']/2,
				    goal['x'] + goal['l']/2,goal['y'] + goal['l']/2,
				    goal['x'] + goal['l']/2,goal['y'] - goal['l']/2]),
			('c3B',(86,109,249)*4))

  #       #添加蓝点
		# self.point = self.batch.add(
  #       	4,pyglet.gl.GL_QUADS,None,   #四边形
  #       	('v2f',[50,50,            #x1,y1
  #       		    50,100,           #x2,y2
  #       		    100,100,		  #x3,y3
  #       		    100,50]),         #x4,y4
  #       	('c3B',(86,109,249)*4))   #color
        
        #添加一条手臂
		self.arm1 = self.batch.add(
        	4,pyglet.gl.GL_QUADS,None,
        	('v2f',[250,250,
        		    250,300,
        		    260,300,
        		    260,250]),
        	('c3B',(249,86,86)*4))     #同上
        
        #添加第二条手臂
		self.arm2 = self.batch.add(
            4, pyglet.gl.GL_QUADS, None,
            ('v2f', [100, 150,              
                     100, 160,
                     200, 160,
                     200, 150]), 
            ('c3B',(249,86,86)*4,))     #同上
        # 画出手臂等
	def render(self):
		self._update_arm()  #更新手臂内容
		self.switch_to()
		self.dispatch_events()
		self.dispatch_event('on_draw')
		self.flip()
    	

        # 刷新并呈现在屏幕上
	def on_draw(self):
		self.clear()   #清屏
		self.batch.draw()  #画上batch里面的内容
        # 刷新手臂等位置
	def _update_arm(self):
		self.goal.vertices = (
			self.goal_info['x'] - self.goal_info['l']/2,self.goal_info['y'] - self.goal_info['l']/2,
			self.goal_info['x'] + self.goal_info['l']/2,self.goal_info['y'] - self.goal_info['l']/2,
			self.goal_info['x'] + self.goal_info['l']/2,self.goal_info['y'] + self.goal_info['l']/2,
			self.goal_info['x'] - self.goal_info['l']/2,self.goal_info['y'] + self.goal_info['l']/2)
		
		#update arm
		(a1l,a2l) = self.arm_info['l']  #半径，arm长度
		(a1r,a2r) = self.arm_info['r']  #弧度，角度
		a1xy = self.center_coord    #a1  start(x0,y0)
		a1xy_ = np.array([np.cos(a1r),np.sin(a1r)]) * a1l + a1xy   #a1 end and a2 start(x1,y1)
		a2xy_ = np.array([np.cos(a1r + a2r),np.sin(a1r + a2r)]) * a2l + a1xy_   #a2 end(x2,y2)

		#第一段手臂的4个点信息
		a1tr,a2tr = np.pi/2 - self.arm_info['r'][0],np.pi/2 - self.arm_info['r'].sum()
		xy01 = a1xy + np.array([-np.cos(a1tr),np.sin(a1tr)]) * self.bar_thc
		xy02 = a1xy + np.array([np.cos(a1tr),-np.sin(a1tr)]) * self.bar_thc
		xy11 = a1xy_ + np.array([np.cos(a1tr),-np.sin(a1tr)]) * self.bar_thc
		xy12 = a1xy_ + np.array([-np.cos(a1tr),np.sin(a1tr)]) * self.bar_thc
        
        #第二个手臂的4个点信息
		xy11_ = a1xy_ + np.array([np.cos(a2tr),-np.sin(a2tr)]) * self.bar_thc
		xy12_ = a1xy_ + np.array([-np.cos(a2tr),np.sin(a2tr)]) * self.bar_thc
		xy21 = a2xy_ + np.array([-np.cos(a2tr),np.sin(a2tr)]) * self.bar_thc
		xy22 = a2xy_ + np.array([np.cos(a2tr),-np.sin(a2tr)]) * self.bar_thc
        
        #将点信息都放入手臂显示中
		self.arm1.vertices = np.concatenate((xy01,xy02,xy11,xy12))
		self.arm2.vertices = np.concatenate((xy11_,xy12_,xy21,xy22))
    
	def on_mouse_motion(self,x,y,dx,dy):
		self.goal_info['x'] = x
		self.goal_info['y'] = y

if __name__ == '__main__':
	env = ArmEnv()
	while True:
		env.render()
		env.step(env.sample_action())