from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

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

