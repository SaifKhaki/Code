# Classification using Ensemble Learning
> This is made during our project of Artificial intelligence and Distributed computing. Collaborators for this repository are all class fellows that worked hard on this project to verify the accuracy of the ensemble learners and their application.

From the idea of performing all the machine learning tasks in labs that took a lot of time and system power to train and then perform a lot better during prediction, we actually wanted to make the learning stage of an ML model as fast as and as resource efficient as the predicting stage. Hence, we actually wanted to develop a solution that could keep the user from wasting its resources on the training of the model, else use our network of peers to train the model and then predict from it.

# Scale Out
This project is built while keeping all the abstractions in a file named [Config.yaml](https://github.com/SaifKhaki/Code/blob/master/config.yaml). Just go to the file and edit your number of regions (i.e. number of supernodes) as well as number of ordinary nodes per region. You can also tune your ip and port of server. Finally, you have the choice to add as many rows of relative addresses of dataset files as you want.
```
datasets:
- Scoring.csv
kazaa:
  o_node_per: 1
  s_nodes: 1
server:
  ip: 192.168.40.189
  port: 4354
```
Finally add your machine learning models code in [node1.ipynb](https://github.com/SaifKhaki/Code/blob/master/node1.ipynb) in the following functions code. This function takes arguments of train data and test data whereas returns the prediction for the test data (we have tested it for a single row in test data).
```
def train_and_predict(df, df2):
    X = df[[i for i in list(df.columns)[:-1]]]
    y = df.Target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
    models = {
        "knn": {"model":KNeighborsClassifier()}
    }

    for name, model in models.items():
        model['model'].fit(X_train, y_train)
        
    models_acc = []
    for name, model in models.items():
        models_acc.append(model["model"].score(X_test, y_test))
    
    for name, model in models.items():
        prediction = model['model'].predict(df2)
        
    return prediction
```

# Dataset used
For our model training and performing bagging concepts, we had to use such a larger dataset that does not give inconsistent predictions when separated to the level of ordinary nodes. It has to be of such length that each node gets a reasonable chunk of the data even after the division across the region. So we used [Scoring.csv](https://github.com/SaifKhaki/Code/blob/master/Scoring.csv). Moreover, the dataset for predicting the results of a goal mostly depends upon the acceleration, velocity and angle of the foot of the striker. These are the main columns used in our dataset. The target column is actually the result of all these parameters.

![image](https://user-images.githubusercontent.com/44811001/123767827-35fdd180-d8e1-11eb-8ae4-270e0ff287fb.png)

As we can see in the above diagram, we have created our dataset of football strikers kicking the ball with a speed, acceleration and some angle. The dataset originally was smaller than this one, which was uniformly extended by keeping the nature of the result assuming that if a ball kicked with 28m/s speed scored a goal, then a ball with 29 m/s will also score it. 
Secondly, about the nature of the data, we can visualize it in the right diagram that the larger sized circlers are located on the “SCORED” line concluding that balls kicked with higher angles scored the goal. Similarly, darker color and moderate acceleration are also located on the vertical line of “SCORED” which clearly satisfies the face that the goal must be scored when the acceleration is not too high and not too low.

# Baseline
The baseline of this project completely revolves around the system resources of the user of our solution. We are actually providing him with a product which could let him train a model on his own uploaded dataset without using his system resources, i.e. only with the help of a faster internet connection. To proof the working nature and the efficiency of the algorithm implemented in our project, we have done a mono-peer testing of the resources used up by the model build up on the same dataset. Mono-peer testing means that we just ran the simple ML algorithm of KNN (which is going to be used in this project) on a single computer and recorded its parameters. 

![image](https://user-images.githubusercontent.com/44811001/123767971-5a59ae00-d8e1-11eb-9de2-415a65d0b19a.png)

The above image shows that for the dataset of football scoring, the model of knn is trained using 130MB of RAM when the dataset was only 5KB. Increasing both parameters proportionally than for a mere dataset of 5MB we would need more than 100 GB of space in memory or permanent storage. Such parameters actually motivated us to build this solution using the ensemble learning strategies in Kazaa architecture. Hence, this became our baseline for the project to make the system more resource efficient by keeping the accuracy of the machine learning model which is,

![image](https://user-images.githubusercontent.com/44811001/123768001-604f8f00-d8e1-11eb-85ee-3afa5883725a.png)

# Results and Analysis
After applying the above proposed approach, we have calculated the amount of RAM usage as well as the accuracy of the whole kazaa architecture as one model. In order to see the competition here, the bagging method used in our approach was a null intersection set bagging which doesn’t have any data point common in the chunks i.e. dataset of one ordinary node is completely different and unknown to the dataset of its neighboring ordinary nodes or their regional supernode. Hence, the final accuracy was calculated by sending a streams of all the available data points (either known or unknown to the node) into the kazaa architecture and following results were achieved:

![image](https://user-images.githubusercontent.com/44811001/123768477-cb996100-d8e1-11eb-9411-917ac284c0e2.png)

We can see, that we again got the same accuracy for our architecture using the ensemble learning as we have used the approach of assigning the most-frequent predictions received as the predicted value. Moreover the ram usage of the user in performing the data uploading task used its internet bandwidth to a reasonable amount but the ram usage was significantly lesser than the original when we used mono-peer.

![image](https://user-images.githubusercontent.com/44811001/123768515-d3f19c00-d8e1-11eb-8c45-e46e80bb725c.png)

# Future Work
For our future work, we are planning to deploy this solution as a web app using flask module of python. Moreover, to avoid the above inconsistencies, we should work with a larger dataset too. Introducing tolerance to the code to avoid the inconsistent scenarios like killing a node, or breaking of anode pipe.

---

### Clone

- Clone this repo to your local machine using `https://github.com/SaifKhaki/Creating-distributed-ML-models-with-Ensemble-Learning.git`

---

## Support
Reach out to us at one of the following places!
- Mail us at 
  - saifbinkhaki.official@gmail.com
  - za7285176@gmail.com
  - aimantahir1225@gmail.com
- Support us on devpost 

---

## License
- GPL 3.0
