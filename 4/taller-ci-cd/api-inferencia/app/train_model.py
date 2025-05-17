import pickle
import yaml
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load parameters from YAML file
with open('params.yaml', 'r') as file:
    config = yaml.safe_load(file)

params = config['model_parameters']

# Load the Iris dataset
iris = load_iris()
X = iris.data
y = iris.target

# Split into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train the Random Forest model
clf = RandomForestClassifier(**params, random_state=42)
clf.fit(X_train, y_train)

# Save the model to a .pkl file
model_filename = 'model.pkl'
with open(model_filename, 'wb') as f:
    pickle.dump(clf, f)

print(f"Model trained and saved as '{model_filename}'")