import argparse
import json
from socket import *
import copy


# Accept parameters from the terminal
def _argparse():
    parser = argparse.ArgumentParser(description='This is description!')
    parser.add_argument('--node', action='store', required=True, dest='node', help='node name')
    return parser.parse_args()


# use to Used to generate the corresponding output file
def getoutput(node, distance, next_hop):
    rout_Graph = {}
    contentOfdict = {}
    for dis_node in distance:
        output_dic = {}
        if dis_node != node:
            output_dic["distance"] = distance[dis_node]
            output_dic["next_hop"] = next_hop[dis_node]
            rout_Graph[dis_node] = output_dic
    f = open(node + '_output.json', 'r')
    content = f.read()
    f.close()
    if len(content) != 0:
        contentOfdict = json.loads(content)
    else:
        g = open(node + '_output.json', 'w')
        json.dump(rout_Graph, g)
        g.close()
    if contentOfdict != rout_Graph:
        g = open(node + '_output.json', 'w')
        # indent = 2 is for json file looks like teacher give
        json.dump(rout_Graph, g, indent=2)
        g.close()

# Reads the graph G and returns a list of its edges and endpoints
def getEdges(G):
    x1 = []  # The starting point
    x2 = []  # The  arrival point
    weight = []  # The weight of the edge from vertex V1 to vertex v2
    for i in G:
        for j in G[i]:
            if G[i][j] != 0:
                weight.append(G[i][j])
                x1.append(i)
                x2.append(j)
    return x1, x2, weight


#  use Bellman-Ford algorithm to calculate shorter distance between node and other node
def Bellman(V, node):
    x1, x2, weight = getEdges(V)
    # set route to find the next_hop of the node when it comes to min distance
    route = [i for i, x in enumerate(x1) if x == node]
    route = [x2[i] for i in route]
    # Initializes the shortest distance between the source point and all points
    distance = dict((k, 10000) for k in V.keys())
    # set the node to be 0 and then to iterate
    distance[node] = 0
    next_hop = dict((k, k) for k in V.keys())
    # The core algorithm
    for k in range(len(V) - 1):  # Cyclic n - 1 round
        check = 0  # Used to mark whether the DIS is updated in the slack of the round
        for i in range(len(weight)):  # One relaxation for each edge
            if distance[x1[i]] + weight[i] < distance[x2[i]]:
                distance[x2[i]] = distance[x1[i]] + weight[i]
                if x1[i] != node:
                    if x1[i] in route:
                        next_hop[x2[i]] = x1[i]
                    else:
                        node = next_hop[x1[i]]
                        while node not in route:
                            pan = next_hop[node]
                        next_hop[x2[i]] = node
                check = 1
        if check == 0:
            break
    getoutput(node, distance, next_hop)
    return distance


def main(): # Initial its bellman graph and send a message to knock up other Router
    parser = _argparse()
    node = parser.node
    h = open(node + '_output.json', 'a')   # create a new json file for out put
    h.close()
    f = open(node + '_distance.json', 'r')
    f1 = f.read()
    f.close()
    distance_dict = json.loads(f1)
    distance_dict[node] = 0
    g = open(node + '_ip.json', 'r')
    g1 = g.read()
    g.close()
    ip_dict = json.loads(g1)
    ip_list = list(ip_dict.keys())
    server_name = ip_dict[node][0]
    sever_port = ip_dict[node][1]
    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.bind(('', sever_port))
    # send own router message to other routers according to port and IP
    # a key to knock up other Router
    for ip_num in range(len(ip_dict)):
        if ip_num != 0:
            json_string = json.dumps(distance_dict)
            udp_socket.sendto(json_string.encode(), (server_name, ip_dict[ip_list[ip_num]][1]))
    last_dic = {}
    print("connect success")
    print('send initial over')
    while True:
        # receive new message from other router and change own message
        message, _ = udp_socket.recvfrom(1024)
        new_dir = json.loads(message.decode())
        first_node = None
        for news in new_dir:
            if new_dir[news] == 0:
                first_node = news
        if node not in last_dic.keys():
            last_dic[node] = distance_dict
        last_dic[first_node] = new_dir
        list1 = [i for i in last_dic]
        V = copy.deepcopy(last_dic)
        for i in last_dic:
            for j in last_dic[i]:
                if j not in list1:
                    V[j] = dict()
        dis = Bellman(V, node)
        # send own own new router message to other routers according to port and IP
        for ip_num in range(len(ip_dict)):
            if ip_num != 0:
                json_string = json.dumps(dis)
                udp_socket.sendto(json_string.encode(), (server_name, ip_dict[ip_list[ip_num]][1]))



if __name__ == '__main__':
    main()
