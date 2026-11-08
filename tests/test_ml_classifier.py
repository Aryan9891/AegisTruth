"""Unit tests for AegisTruth Calibrated Machine Learning Classifier & Training Pipeline."""

import numpy as np
from PIL import Image
from aegistruth.core.ml_classifier import (
    CalibratedForensicClassifier,
    extract_image_features,
    FEATURE_NAMES,
    get_calibrated_classifier
)
from aegistruth.core.train_forensic_classifier import (
    generate_synthetic_benchmark_dataset,
    evaluate_model,
    train_and_save_pipeline
)

def test_feature_extraction():
    img = Image.new("RGB", (64, 64), color=(120, 80, 200))
    feats = extract_image_features(img)
    assert isinstance(feats, np.ndarray)
    assert len(feats) == len(FEATURE_NAMES)
    assert feats.dtype == np.float64

def test_classifier_fit_and_predict():
    clf = CalibratedForensicClassifier()
    X, y = generate_synthetic_benchmark_dataset(num_samples=500, random_seed=42)
    fit_res = clf.fit(X, y, l2_reg=0.01)

    assert fit_res["converged"] is True
    assert fit_res["accuracy"] > 0.90
    assert fit_res["samples_trained"] == 500

    probs = clf.predict_proba(X[:10])
    assert probs.shape == (10,)
    assert np.all((probs >= 0.0) & (probs <= 1.0))

    preds = clf.predict(X[:10])
    assert len(preds) == 10
    assert set(preds).issubset({0, 1})

def test_classifier_save_load(tmp_path):
    clf = CalibratedForensicClassifier()
    X, y = generate_synthetic_benchmark_dataset(num_samples=200, random_seed=7)
    clf.fit(X, y)

    weight_file = tmp_path / "test_weights.json"
    clf.save(weight_file)
    assert weight_file.exists()

    loaded_clf = CalibratedForensicClassifier.load(weight_file)
    np.testing.assert_allclose(clf.weights, loaded_clf.weights)
    assert clf.bias == loaded_clf.bias

    orig_probs = clf.predict_proba(X[:5])
    loaded_probs = loaded_clf.predict_proba(X[:5])
    np.testing.assert_allclose(orig_probs, loaded_probs)

def test_classifier_explanation():
    clf = get_calibrated_classifier()
    X, _ = generate_synthetic_benchmark_dataset(num_samples=10, random_seed=12)
    explanation = clf.explain(X[0])

    assert len(explanation) == len(FEATURE_NAMES)
    assert "feature" in explanation[0]
    assert "importance_attribution" in explanation[0]
    assert explanation[0]["indicates"] in ["SYNTHETIC", "AUTHENTIC"]

def test_benchmark_evaluation():
    clf = CalibratedForensicClassifier()
    X, y = generate_synthetic_benchmark_dataset(num_samples=400, random_seed=99)
    clf.fit(X[:300], y[:300])

    metrics = evaluate_model(clf, X[300:], y[300:])
    assert metrics["accuracy"] >= 0.90
    assert metrics["precision"] >= 0.90
    assert metrics["recall"] >= 0.90
    assert metrics["f1_score"] >= 0.90


def test_video_classifier_fit_and_predict():
    from aegistruth.core.ml_classifier import CalibratedVideoClassifier, VIDEO_FEATURE_NAMES, get_calibrated_video_classifier
    from aegistruth.core.train_forensic_classifier import generate_video_benchmark_dataset

    clf = CalibratedVideoClassifier()
    X, y = generate_video_benchmark_dataset(num_samples=400, random_seed=42)
    fit_res = clf.fit(X, y, l2_reg=0.01)

    assert fit_res["converged"] is True
    assert fit_res["accuracy"] > 0.95
    assert fit_res["samples_trained"] == 400

    probs = clf.predict_proba(X[:10])
    assert probs.shape == (10,)
    assert np.all((probs >= 0.0) & (probs <= 1.0))

    expl = clf.explain(X[0])
    assert len(expl) == len(VIDEO_FEATURE_NAMES)
    assert expl[0]["indicates"] in ["SYNTHETIC", "AUTHENTIC"]


def test_video_classifier_save_load(tmp_path):
    from aegistruth.core.ml_classifier import CalibratedVideoClassifier
    from aegistruth.core.train_forensic_classifier import generate_video_benchmark_dataset

    clf = CalibratedVideoClassifier()
    X, y = generate_video_benchmark_dataset(num_samples=200, random_seed=15)
    clf.fit(X, y)

    target = tmp_path / "video_weights.json"
    clf.save(target)
    assert target.exists()

    loaded = CalibratedVideoClassifier.load(target)
    np.testing.assert_allclose(clf.weights, loaded.weights)
    assert clf.bias == loaded.bias
    np.testing.assert_allclose(clf.predict_proba(X[:5]), loaded.predict_proba(X[:5]))

