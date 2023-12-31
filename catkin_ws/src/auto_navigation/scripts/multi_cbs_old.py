#!/usr/bin/env python3

import rospy
import math
import threading
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from tf.transformations import euler_from_quaternion, quaternion_from_euler
from geometry_msgs.msg import PoseStamped
import yaml

rospy.init_node('goal_pose')

def check_goal_reached(init_pose, goal_coor, bias):
    if (init_pose.pose.position.x > goal_coor[0] - bias and init_pose.pose.position.x < goal_coor[0] + bias
            and init_pose.pose.position.y > goal_coor[1] - bias and init_pose.pose.position.y < goal_coor[1] + bias):
        return True
    else:
        return False

def control_agent(agent_id, init_pose, coordinates, scale):
    topic_name = f'agent{agent_id}/cmd_vel'
    cmd_pub = rospy.Publisher(topic_name, Twist, queue_size=10)
    init_x = init_pose.pose.position.x
    init_y = init_pose.pose.position.y

    twist = Twist()

    for coordinate in coordinates:
        goal_x = coordinate[0] * scale + init_x
        goal_y = coordinate[1] * -scale + init_y

        while not check_goal_reached(init_pose, [goal_x, goal_y], 0.02):
            init_pose = rospy.wait_for_message(f'/id{agent_id}/aruco_single/pose', PoseStamped)
            orientation_q = init_pose.pose.orientation
            orientation_list = [orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w]
            (roll, pitch, yaw) = euler_from_quaternion(orientation_list)
            Orientation = yaw
            dx = goal_x - init_pose.pose.position.x
            dy = goal_y - init_pose.pose.position.y
            distance = math.dist([init_pose.pose.position.x, init_pose.pose.position.y], [goal_x, goal_y])
            goal_direct = math.atan2(dy, dx)

            print(f"Agent {agent_id}: current_coor", [init_pose.pose.position.x, init_pose.pose.position.y])
            print(f"Agent {agent_id}: goal_coor", [goal_x, goal_y])
            print(f"Agent {agent_id}: Orientation", Orientation)
            print(f"Agent {agent_id}: goal_direct", goal_direct)

            if (Orientation < 0):
                Orientation = Orientation + 2 * math.pi
            if (goal_direct < 0):
                goal_direct = goal_direct + 2 * math.pi

            theta = goal_direct - Orientation

            if theta < 0 and abs(theta) > abs(theta + 2 * math.pi):
                theta = theta + 2 * math.pi
            elif theta > 0 and abs(theta - 2 * math.pi) < theta:
                theta = theta - 2 * math.pi

            print(f"Agent {agent_id}: theta:", theta)

            k2 = 5
            linear = 2
            angular = k2 * theta
            twist.linear.x = linear * distance * math.cos(theta)
            twist.angular.z = -angular
            cmd_pub.publish(twist)

# Read the YAML data from the file for agent 1 (schedule 1)
with open("/home/zeyu/catkin_ws/src/auto_navigation/scripts/cbs_output.yaml", "r") as yaml_file:
    yaml_data = yaml.safe_load(yaml_file)

# Extract coordinates for agent 1 (schedule 1)
agent_1_schedule = yaml_data["schedule"][1]

# Initialize a list to store the coordinates for agent 1
coordinates_1 = []

# Iterate through the schedule and extract x, y values for agent 1
for item in agent_1_schedule:
    x = item["x"]
    y = item["y"]
    coordinates_1.append([x - 8, y - 9])  # Subtract 8 from x and 9 from y

# Read the YAML data from the file for agent 2 (schedule 2)
# Replace the file path with the correct one for agent 2
with open("/home/zeyu/catkin_ws/src/auto_navigation/scripts/cbs_output.yaml", "r") as yaml_file:
    yaml_data = yaml.safe_load(yaml_file)

# Extract coordinates for agent 2 (schedule 2)
agent_2_schedule = yaml_data["schedule"][2]

# Initialize a list to store the coordinates for agent 2
coordinates_2 = []

# Iterate through the schedule and extract x, y values for agent 2
for item in agent_2_schedule:
    x = item["x"]
    y = item["y"]
    coordinates_2.append([x, y - 9])  # Subtract 8 from x and 9 from y

# Define the scale for both agents (you can adjust this as needed)
scale = 0.08

init_pose_1 = rospy.wait_for_message('/id321/aruco_single/pose', PoseStamped)
init_pose_2 = rospy.wait_for_message('/id325/aruco_single/pose', PoseStamped)

threads = []
t1 = threading.Thread(target=control_agent, args=(321, init_pose_1, coordinates_1, scale))
threads.append(t1)
t1.start()
t2 = threading.Thread(target=control_agent, args=(325, init_pose_2, coordinates_2, scale))
threads.append(t2)
t2.start()
for t in threads:
    t.join()

# Control Agent 1
# control_agent(init_pose_1, coordinates_1, scale)

# Control Agent 2
# You may want to set the initial pose for Agent 2 if it's different from Agent 1
# control_agent(init_pose_for_agent_2, coordinates_2, scale)

rospy.spin()

