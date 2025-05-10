from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.ensemble import RandomForestClassifier
import mlflow
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_score
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


def custom_reports(model, X, y):
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)

    print('* Classification Report:')
    print(classification_report(y, y_pred))

    print('* Confusion Matrix:')
    print(confusion_matrix(y, y_pred))

    accuracy = accuracy_score(y, y_pred)
    auroc = roc_auc_score(y, y_proba, multi_class='ovo')
    precision_value = precision_score(y, y_pred, average='macro')
    recall_value = recall_score(y, y_pred, average='macro')
    f1 = f1_score(y, y_pred, average='macro')

    print(f'\nAUROC: {auroc:.4f}')
    print(f'Accuracy: {accuracy:.4f}')
    print(f'Recall: {recall_value:.4f}')
    print(f'Precision: {precision_value:.4f}')
    print(f'F1 Score: {f1:.4f}')
    
    # Create the metrics dictionary
    metrics = {
        "test_accuracy": accuracy,
        "test_roc_auc": auroc,
        "test_precision": precision_value,
        "test_recall": recall_value,
        "test_f1_score": f1,
    }
    
    return metrics

def champion_callback(study, frozen_trial):
  """
  Logging callback that will report when a new trial iteration improves upon existing
  best trial values.

  Note: This callback is not intended for use in distributed computing systems such as Spark
  or Ray due to the micro-batch iterative implementation for distributing trials to a cluster's
  workers or agents.
  The race conditions with file system state management for distributed trials will render
  inconsistent values with this callback.
  """

  winner = study.user_attrs.get("winner", None)

  if study.best_value and winner != study.best_value:
      study.set_user_attr("winner", study.best_value)
      if winner:
          improvement_percent = (abs(winner - study.best_value) / study.best_value) * 100
          print(
              f"Trial {frozen_trial.number} achieved value: {frozen_trial.value} with "
              f"{improvement_percent: .4f}% improvement"
          )
      else:
          print(f"Initial trial {frozen_trial.number} achieved value: {frozen_trial.value}")

def make_objective_rf_acc(X, y, preprocessor):
    def objective_rf_acc(trial):
        with mlflow.start_run(nested=True):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 600), 
                'max_depth': trial.suggest_int('max_depth', 3, 30), 
                'min_samples_split': trial.suggest_int('min_samples_split', 3, 20), 
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 3, 20), 
                'max_features': trial.suggest_float('max_features', 0.5, 1.0),
                'max_samples': trial.suggest_float('max_samples', 0.7, 1.0)
            }

            clf = Pipeline([
                ("preprocess", preprocessor),
                ("model", RandomForestClassifier(**params, random_state=42, n_jobs=-1))
            ])

            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

            acc_scores = cross_val_score(clf, X, y, cv=skf, scoring="accuracy", n_jobs=-1)
            auroc_scores = cross_val_score(clf, X, y, cv=skf, scoring="roc_auc_ovo", n_jobs=-1)

            mlflow.log_params(params)
            mlflow.log_metric("mean_accuracy", np.mean(acc_scores))
            mlflow.log_metric("mean_auroc", np.mean(auroc_scores))

            return np.mean(acc_scores)
    return objective_rf_acc

def make_objective_rf_auroc(X, y, preprocessor):
    def objective_rf_auroc(trial):
        with mlflow.start_run(nested=True):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 600), 
                'max_depth': trial.suggest_int('max_depth', 3, 30), 
                'min_samples_split': trial.suggest_int('min_samples_split', 3, 20), 
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 3, 20), 
                'max_features': trial.suggest_float('max_features', 0.5, 1.0),
                'max_samples': trial.suggest_float('max_samples', 0.7, 1.0)
            }

            clf = Pipeline([
                ("preprocess", preprocessor),
                ("model", RandomForestClassifier(**params, random_state=42, n_jobs=-1))
            ])

            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

            auroc_scores = cross_val_score(clf, X, y, cv=skf, scoring="roc_auc_ovo", n_jobs=-1)
            acc_scores = cross_val_score(clf, X, y, cv=skf, scoring="accuracy", n_jobs=-1)

            mlflow.log_params(params)
            mlflow.log_metric("mean_auroc", np.mean(auroc_scores))
            mlflow.log_metric("mean_accuracy", np.mean(acc_scores))

            return np.mean(auroc_scores)
    return objective_rf_auroc