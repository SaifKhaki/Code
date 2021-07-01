X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
models = {
    "KNN": {"model":KNeighborsClassifier()}
}