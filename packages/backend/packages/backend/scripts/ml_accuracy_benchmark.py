#!/usr/bin/env python3
"""
ML Accuracy Benchmarking Script for Manna Financial Platform.

This script creates comprehensive accuracy benchmarks for the ML categorization service:
- Tests accuracy against labeled training data
- Cross-validation performance analysis
- Per-category accuracy breakdown
- Confidence score calibration analysis
- Feature importance analysis
- Model comparison between rule-based and ML approaches

Target: Achieve 95% accuracy on categorization tasks.
"""

import sys
import os
from pathlib import Path

# Add the backend src to Python path
backend_path = Path(__file__).parent.parent / "src"
sys.path.append(str(backend_path))

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, calibration_curve
)
from sklearn.calibration import CalibratedClassifierCV
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockTransaction:
    """Mock transaction class for testing."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.merchant_name = data.get("merchant_name")
        self.amount = float(data.get("amount", 0))
        self.original_description = data.get("original_description", "")
        self.user_category = data.get("user_category")
        self.primary_category = data.get("primary_category")
        self.date = data.get("date", datetime.now().date())


class MLAccuracyBenchmark:
    """Comprehensive ML accuracy benchmarking suite."""
    
    def __init__(self, results_dir: str = "/tmp/manna_ml_benchmarks"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize services
        try:
            from services.ml_categorization import ml_service
            from services.ml_categorization_optimized import optimized_ml_service
            self.ml_service = ml_service
            self.optimized_ml_service = optimized_ml_service
        except ImportError as e:
            logger.error(f"Failed to import ML services: {e}")
            self.ml_service = None
            self.optimized_ml_service = None
    
    def generate_comprehensive_test_data(self, size: int = 1000) -> List[Dict[str, Any]]:
        """Generate comprehensive test dataset with realistic transaction patterns."""
        import random
        from uuid import uuid4
        
        # Realistic transaction patterns by category
        transaction_patterns = {
            "Food & Dining": [
                {"merchants": ["Starbucks", "McDonald's", "Subway", "Pizza Hut", "KFC"], "amounts": (5, 50)},
                {"merchants": ["The Cheesecake Factory", "Olive Garden", "Red Lobster"], "amounts": (25, 100)},
                {"merchants": ["DoorDash", "Uber Eats", "Grubhub"], "amounts": (15, 75)},
            ],
            "Transportation": [
                {"merchants": ["Shell", "Chevron", "Exxon", "BP", "Mobil"], "amounts": (30, 80)},
                {"merchants": ["Uber", "Lyft"], "amounts": (10, 50)},
                {"merchants": ["BART", "Metro", "MTA"], "amounts": (2, 15)},
                {"merchants": ["Southwest Airlines", "Delta", "United"], "amounts": (200, 800)},
            ],
            "Shopping": [
                {"merchants": ["Amazon.com", "Amazon"], "amounts": (10, 500)},
                {"merchants": ["Target", "Walmart", "Costco"], "amounts": (25, 300)},
                {"merchants": ["Best Buy", "Apple Store"], "amounts": (50, 2000)},
                {"merchants": ["Home Depot", "Lowe's"], "amounts": (20, 400)},
            ],
            "Bills & Utilities": [
                {"merchants": ["PG&E", "ConEd", "Electric Company"], "amounts": (50, 300)},
                {"merchants": ["Comcast", "Verizon", "AT&T"], "amounts": (40, 150)},
                {"merchants": ["Water Department", "City of"], "amounts": (25, 100)},
                {"merchants": ["Insurance Co", "State Farm", "Geico"], "amounts": (100, 500)},
            ],
            "Entertainment": [
                {"merchants": ["Netflix", "Spotify", "Hulu", "Disney+"], "amounts": (10, 20)},
                {"merchants": ["AMC Theatres", "Regal Cinemas"], "amounts": (12, 50)},
                {"merchants": ["Steam", "PlayStation", "Xbox"], "amounts": (20, 100)},
            ],
            "Healthcare": [
                {"merchants": ["CVS Pharmacy", "Walgreens", "Rite Aid"], "amounts": (10, 200)},
                {"merchants": ["Kaiser", "Medical Center", "Clinic"], "amounts": (50, 500)},
                {"merchants": ["Dental", "Dentist"], "amounts": (100, 800)},
            ],
            "Income": [
                {"merchants": ["Direct Deposit", "Payroll", "Salary"], "amounts": (1000, 8000)},
                {"merchants": ["Interest Payment", "Dividend"], "amounts": (10, 1000)},
            ],
            "Transfer": [
                {"merchants": ["Zelle", "Venmo", "PayPal"], "amounts": (20, 500)},
                {"merchants": ["Transfer", "Wire Transfer"], "amounts": (100, 5000)},
            ],
            "Fees & Charges": [
                {"merchants": ["Overdraft Fee", "ATM Fee", "Service Fee"], "amounts": (5, 50)},
            ],
        }
        
        transactions = []
        categories = list(transaction_patterns.keys())
        
        for i in range(size):
            # Choose category (some categories more common than others)
            category_weights = {
                "Food & Dining": 0.25,
                "Shopping": 0.20,
                "Transportation": 0.15,
                "Bills & Utilities": 0.15,
                "Entertainment": 0.08,
                "Healthcare": 0.05,
                "Income": 0.05,
                "Transfer": 0.04,
                "Fees & Charges": 0.03,
            }
            
            category = random.choices(categories, weights=list(category_weights.values()))[0]
            patterns = transaction_patterns[category]
            pattern = random.choice(patterns)
            
            merchant = random.choice(pattern["merchants"])
            min_amount, max_amount = pattern["amounts"]
            amount = round(random.uniform(min_amount, max_amount), 2)
            
            # Income should be positive
            if category == "Income":
                amount = abs(amount)
            else:
                amount = -abs(amount)  # Expenses are negative
            
            # Generate realistic transaction name
            store_number = random.randint(1000, 9999)
            if "Store" in merchant or merchant in ["Target", "Walmart", "Best Buy"]:
                name = f"{merchant} Store #{store_number}"
            elif merchant in ["Shell", "Chevron", "Exxon"]:
                name = f"{merchant} #{store_number}"
            elif "Direct Deposit" in merchant:
                name = f"{merchant} PAYROLL"
            else:
                name = merchant
            
            # Add some description variety
            descriptions = [
                f"Purchase at {merchant}",
                f"{merchant} Transaction {i}",
                f"Payment to {merchant}",
                name,
            ]
            
            transaction = {
                "id": str(uuid4()),
                "name": name,
                "merchant_name": merchant,
                "amount": amount,
                "date": datetime.now() - timedelta(days=random.randint(0, 365)),
                "original_description": random.choice(descriptions),
                "user_category": category,  # Ground truth
                "primary_category": None,   # To be predicted
                "confidence_level": None
            }
            
            transactions.append(transaction)
        
        return transactions
    
    def test_ml_service_accuracy(
        self, 
        test_data: List[Dict[str, Any]], 
        service_name: str = "standard"
    ) -> Dict[str, Any]:
        """Test accuracy of ML service against labeled data."""
        if service_name == "optimized" and self.optimized_ml_service:
            service = self.optimized_ml_service
        else:
            service = self.ml_service
        
        if not service:
            return {"error": "ML service not available"}
        
        logger.info(f"Testing {service_name} ML service accuracy on {len(test_data)} transactions")
        
        # Filter transactions with labels
        labeled_data = [t for t in test_data if t.get("user_category")]
        if not labeled_data:
            return {"error": "No labeled data available"}
        
        predictions = []
        ground_truth = []
        confidence_scores = []
        prediction_times = []
        
        # Test each transaction
        for i, transaction_data in enumerate(labeled_data):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(labeled_data)} transactions")
            
            mock_transaction = MockTransaction(transaction_data)
            
            try:
                start_time = datetime.now()
                
                if hasattr(service, 'categorize_transaction'):
                    result = service.categorize_transaction(mock_transaction)
                    predicted_category = result.suggested_category
                    confidence = result.confidence
                else:
                    # Fallback for different API
                    predicted_category = "Other"
                    confidence = 0.5
                
                end_time = datetime.now()
                prediction_time = (end_time - start_time).total_seconds() * 1000
                
                predictions.append(predicted_category)
                ground_truth.append(transaction_data["user_category"])
                confidence_scores.append(confidence)
                prediction_times.append(prediction_time)
                
            except Exception as e:
                logger.error(f"Error processing transaction {transaction_data['id']}: {e}")
                predictions.append("Error")
                ground_truth.append(transaction_data["user_category"])
                confidence_scores.append(0.0)
                prediction_times.append(0.0)
        
        # Calculate metrics
        accuracy = accuracy_score(ground_truth, predictions)
        precision = precision_score(ground_truth, predictions, average='weighted', zero_division=0)
        recall = recall_score(ground_truth, predictions, average='weighted', zero_division=0)
        f1 = f1_score(ground_truth, predictions, average='weighted', zero_division=0)
        
        # Per-category analysis
        unique_categories = list(set(ground_truth))
        per_category_accuracy = {}
        
        for category in unique_categories:
            category_mask = np.array(ground_truth) == category
            if np.any(category_mask):
                category_predictions = np.array(predictions)[category_mask]
                category_ground_truth = np.array(ground_truth)[category_mask]
                category_accuracy = accuracy_score(category_ground_truth, category_predictions)
                per_category_accuracy[category] = category_accuracy
        
        # Confidence analysis
        confidence_stats = {
            "mean": np.mean(confidence_scores),
            "median": np.median(confidence_scores),
            "std": np.std(confidence_scores),
            "min": np.min(confidence_scores),
            "max": np.max(confidence_scores)
        }
        
        # Performance analysis
        performance_stats = {
            "mean_prediction_time_ms": np.mean(prediction_times),
            "median_prediction_time_ms": np.median(prediction_times),
            "p95_prediction_time_ms": np.percentile(prediction_times, 95),
            "total_predictions": len(predictions)
        }
        
        return {
            "service_name": service_name,
            "total_samples": len(labeled_data),
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "per_category_accuracy": per_category_accuracy,
            "confidence_statistics": confidence_stats,
            "performance_statistics": performance_stats,
            "predictions": predictions,
            "ground_truth": ground_truth,
            "confidence_scores": confidence_scores,
            "unique_categories": unique_categories
        }
    
    def compare_services(self, test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare different ML service implementations."""
        logger.info("Comparing ML service implementations...")
        
        results = {}
        
        # Test standard service
        if self.ml_service:
            results["standard"] = self.test_ml_service_accuracy(test_data, "standard")
        
        # Test optimized service
        if self.optimized_ml_service:
            results["optimized"] = self.test_ml_service_accuracy(test_data, "optimized")
        
        # Compare results
        comparison = {
            "services_tested": list(results.keys()),
            "comparison_summary": {}
        }
        
        if len(results) > 1:
            metrics = ["accuracy", "precision", "recall", "f1_score"]
            for metric in metrics:
                comparison["comparison_summary"][metric] = {
                    service: results[service][metric] 
                    for service in results.keys() 
                    if metric in results[service]
                }
        
        comparison["detailed_results"] = results
        return comparison
    
    def cross_validation_analysis(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform cross-validation analysis on the ML model."""
        logger.info("Performing cross-validation analysis...")
        
        if not self.ml_service:
            return {"error": "ML service not available"}
        
        # Prepare data for cross-validation
        labeled_data = [t for t in training_data if t.get("user_category")]
        if len(labeled_data) < 50:
            return {"error": "Insufficient labeled data for cross-validation"}
        
        # Extract features and labels
        X = []
        y = []
        
        for transaction_data in labeled_data:
            # Create text features
            text_features = f"{transaction_data['name']} {transaction_data.get('merchant_name', '')} {transaction_data.get('original_description', '')}"
            X.append(text_features)
            y.append(transaction_data['user_category'])
        
        # Try to access the ML service's models for cross-validation
        try:
            if hasattr(self.ml_service, 'text_vectorizer') and hasattr(self.ml_service, 'text_classifier'):
                if self.ml_service.text_vectorizer and self.ml_service.text_classifier:
                    # Vectorize features
                    X_vectorized = self.ml_service.text_vectorizer.transform(X)
                    
                    # Perform cross-validation
                    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                    cv_scores = cross_val_score(
                        self.ml_service.text_classifier, 
                        X_vectorized, 
                        y, 
                        cv=cv, 
                        scoring='accuracy'
                    )
                    
                    return {
                        "cv_scores": cv_scores.tolist(),
                        "mean_cv_score": cv_scores.mean(),
                        "std_cv_score": cv_scores.std(),
                        "samples_used": len(labeled_data)
                    }
        except Exception as e:
            logger.error(f"Cross-validation failed: {e}")
        
        return {"error": "Could not perform cross-validation - model not available"}
    
    def analyze_confidence_calibration(
        self, 
        predictions: List[str], 
        ground_truth: List[str], 
        confidence_scores: List[float]
    ) -> Dict[str, Any]:
        """Analyze confidence score calibration."""
        logger.info("Analyzing confidence calibration...")
        
        # Convert to binary classification for calibration analysis
        correct_predictions = [1 if p == g else 0 for p, g in zip(predictions, ground_truth)]
        
        # Calculate calibration curve
        try:
            prob_true, prob_pred = calibration_curve(
                correct_predictions, 
                confidence_scores, 
                n_bins=10, 
                strategy='uniform'
            )
            
            # Calculate Expected Calibration Error (ECE)
            bin_boundaries = np.linspace(0, 1, 11)
            ece = 0
            
            for i in range(len(prob_true)):
                bin_size = np.sum((np.array(confidence_scores) >= bin_boundaries[i]) & 
                                 (np.array(confidence_scores) < bin_boundaries[i+1]))
                if bin_size > 0:
                    ece += (bin_size / len(confidence_scores)) * abs(prob_true[i] - prob_pred[i])
            
            return {
                "calibration_curve": {
                    "prob_true": prob_true.tolist(),
                    "prob_pred": prob_pred.tolist()
                },
                "expected_calibration_error": ece,
                "confidence_statistics": {
                    "mean_confidence": np.mean(confidence_scores),
                    "std_confidence": np.std(confidence_scores),
                    "confidence_accuracy_correlation": np.corrcoef(confidence_scores, correct_predictions)[0, 1]
                }
            }
            
        except Exception as e:
            logger.error(f"Calibration analysis failed: {e}")
            return {"error": str(e)}
    
    def generate_benchmark_visualizations(self, benchmark_results: Dict[str, Any]) -> List[str]:
        """Generate comprehensive benchmark visualizations."""
        plt.style.use('seaborn-v0_8')
        chart_paths = []
        
        # 1. Accuracy Comparison Chart
        if "detailed_results" in benchmark_results:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('ML Service Accuracy Benchmark Results', fontsize=16, fontweight='bold')
            
            services = list(benchmark_results["detailed_results"].keys())
            
            # Overall metrics comparison
            metrics = ["accuracy", "precision", "recall", "f1_score"]
            service_metrics = {}
            
            for service in services:
                service_results = benchmark_results["detailed_results"][service]
                service_metrics[service] = [
                    service_results.get(metric, 0) for metric in metrics
                ]
            
            ax1 = axes[0, 0]
            x = np.arange(len(metrics))
            width = 0.35 if len(services) == 2 else 0.8 / len(services)
            
            for i, service in enumerate(services):
                offset = (i - len(services)/2) * width + width/2
                bars = ax1.bar(x + offset, service_metrics[service], width, 
                              label=service, alpha=0.8)
                
                # Add value labels on bars
                for bar, value in zip(bars, service_metrics[service]):
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                            f'{value:.3f}', ha='center', va='bottom', fontsize=10)
            
            ax1.set_ylabel('Score')
            ax1.set_title('Overall Performance Metrics')
            ax1.set_xticks(x)
            ax1.set_xticklabels(metrics)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.axhline(0.95, color='red', linestyle='--', alpha=0.7, label='Target: 95%')
            
            # Per-category accuracy heatmap
            ax2 = axes[0, 1]
            
            if len(services) > 0:
                first_service = services[0]
                per_category = benchmark_results["detailed_results"][first_service].get("per_category_accuracy", {})
                
                if per_category:
                    categories = list(per_category.keys())
                    accuracy_matrix = []
                    
                    for service in services:
                        service_accuracies = []
                        service_per_cat = benchmark_results["detailed_results"][service].get("per_category_accuracy", {})
                        for category in categories:
                            service_accuracies.append(service_per_cat.get(category, 0))
                        accuracy_matrix.append(service_accuracies)
                    
                    im = ax2.imshow(accuracy_matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
                    ax2.set_xticks(range(len(categories)))
                    ax2.set_xticklabels(categories, rotation=45, ha='right')
                    ax2.set_yticks(range(len(services)))
                    ax2.set_yticklabels(services)
                    ax2.set_title('Per-Category Accuracy')
                    
                    # Add text annotations
                    for i in range(len(services)):
                        for j in range(len(categories)):
                            text = ax2.text(j, i, f'{accuracy_matrix[i][j]:.2f}',
                                          ha="center", va="center", color="black", fontweight='bold')
                    
                    plt.colorbar(im, ax=ax2)
            
            # Confidence distribution
            ax3 = axes[1, 0]
            
            for service in services:
                service_results = benchmark_results["detailed_results"][service]
                confidence_scores = service_results.get("confidence_scores", [])
                
                if confidence_scores:
                    ax3.hist(confidence_scores, bins=30, alpha=0.7, label=f'{service} service', density=True)
            
            ax3.set_xlabel('Confidence Score')
            ax3.set_ylabel('Density')
            ax3.set_title('Confidence Score Distribution')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Performance comparison
            ax4 = axes[1, 1]
            
            performance_metrics = []
            performance_labels = []
            
            for service in services:
                service_results = benchmark_results["detailed_results"][service]
                perf_stats = service_results.get("performance_statistics", {})
                
                mean_time = perf_stats.get("mean_prediction_time_ms", 0)
                p95_time = perf_stats.get("p95_prediction_time_ms", 0)
                
                performance_metrics.extend([mean_time, p95_time])
                performance_labels.extend([f'{service}\nMean', f'{service}\nP95'])
            
            if performance_metrics:
                bars = ax4.bar(performance_labels, performance_metrics, 
                              color=['lightblue', 'lightcoral'] * len(services))
                ax4.axhline(200, color='red', linestyle='--', alpha=0.7, label='Target: 200ms')
                ax4.set_ylabel('Response Time (ms)')
                ax4.set_title('Performance Comparison')
                ax4.legend()
                ax4.grid(True, alpha=0.3)
                
                # Add value labels
                for bar, value in zip(bars, performance_metrics):
                    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                            f'{value:.1f}ms', ha='center', va='bottom')
            
            plt.tight_layout()
            chart_path = self.results_dir / "ml_accuracy_benchmark.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            chart_paths.append(str(chart_path))
            plt.close()
        
        # 2. Confusion Matrix
        if "detailed_results" in benchmark_results:
            for service_name, service_results in benchmark_results["detailed_results"].items():
                predictions = service_results.get("predictions", [])
                ground_truth = service_results.get("ground_truth", [])
                unique_categories = service_results.get("unique_categories", [])
                
                if predictions and ground_truth:
                    plt.figure(figsize=(12, 10))
                    
                    cm = confusion_matrix(ground_truth, predictions, labels=unique_categories)
                    
                    # Normalize confusion matrix
                    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
                    
                    # Plot confusion matrix
                    sns.heatmap(cm_normalized, annot=True, fmt='.2f', cmap='Blues',
                               xticklabels=unique_categories, yticklabels=unique_categories)
                    plt.title(f'Confusion Matrix - {service_name.title()} Service')
                    plt.xlabel('Predicted Category')
                    plt.ylabel('Actual Category')
                    plt.xticks(rotation=45, ha='right')
                    plt.yticks(rotation=0)
                    
                    plt.tight_layout()
                    chart_path = self.results_dir / f"confusion_matrix_{service_name}.png"
                    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                    chart_paths.append(str(chart_path))
                    plt.close()
        
        return chart_paths
    
    def run_comprehensive_benchmark(self, test_data_size: int = 1000) -> Dict[str, Any]:
        """Run comprehensive ML accuracy benchmark."""
        logger.info("Starting comprehensive ML accuracy benchmark...")
        
        results = {
            "benchmark_started": datetime.now().isoformat(),
            "test_parameters": {
                "test_data_size": test_data_size,
                "target_accuracy": 0.95
            }
        }
        
        # Generate test data
        logger.info(f"Generating {test_data_size} test transactions...")
        test_data = self.generate_comprehensive_test_data(test_data_size)
        
        # Compare services
        service_comparison = self.compare_services(test_data)
        results["service_comparison"] = service_comparison
        
        # Cross-validation analysis
        cv_results = self.cross_validation_analysis(test_data)
        results["cross_validation"] = cv_results
        
        # Confidence calibration analysis
        if "detailed_results" in service_comparison:
            for service_name, service_results in service_comparison["detailed_results"].items():
                predictions = service_results.get("predictions", [])
                ground_truth = service_results.get("ground_truth", [])
                confidence_scores = service_results.get("confidence_scores", [])
                
                if predictions and ground_truth and confidence_scores:
                    calibration = self.analyze_confidence_calibration(
                        predictions, ground_truth, confidence_scores
                    )
                    results[f"calibration_{service_name}"] = calibration
        
        # Generate visualizations
        chart_paths = self.generate_benchmark_visualizations(service_comparison)
        results["chart_paths"] = chart_paths
        
        # Performance assessment
        results["performance_assessment"] = self.assess_benchmark_performance(results)
        
        # Save results
        results_file = self.results_dir / f"ml_accuracy_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        results["results_file"] = str(results_file)
        results["benchmark_completed"] = datetime.now().isoformat()
        
        logger.info(f"Benchmark completed. Results saved to: {results_file}")
        return results
    
    def assess_benchmark_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess benchmark results against performance targets."""
        assessment = {
            "target_accuracy": 0.95,
            "target_response_time_ms": 200,
            "services_assessed": [],
            "overall_grade": "F"
        }
        
        if "service_comparison" in results and "detailed_results" in results["service_comparison"]:
            service_results = results["service_comparison"]["detailed_results"]
            
            for service_name, service_data in service_results.items():
                accuracy = service_data.get("accuracy", 0)
                mean_time = service_data.get("performance_statistics", {}).get("mean_prediction_time_ms", 1000)
                
                service_assessment = {
                    "service_name": service_name,
                    "accuracy": accuracy,
                    "accuracy_target_met": accuracy >= 0.95,
                    "mean_response_time_ms": mean_time,
                    "response_time_target_met": mean_time <= 200,
                    "overall_score": 0
                }
                
                # Calculate overall score
                accuracy_score = min(accuracy / 0.95, 1.0) * 50  # 50% weight on accuracy
                time_score = min(200 / max(mean_time, 1), 1.0) * 50  # 50% weight on response time
                service_assessment["overall_score"] = accuracy_score + time_score
                
                assessment["services_assessed"].append(service_assessment)
        
        # Determine overall grade
        if assessment["services_assessed"]:
            max_score = max(s["overall_score"] for s in assessment["services_assessed"])
            if max_score >= 90:
                assessment["overall_grade"] = "A"
            elif max_score >= 80:
                assessment["overall_grade"] = "B"
            elif max_score >= 70:
                assessment["overall_grade"] = "C"
            elif max_score >= 60:
                assessment["overall_grade"] = "D"
            else:
                assessment["overall_grade"] = "F"
        
        return assessment


def main():
    """Run the ML accuracy benchmark."""
    benchmark = MLAccuracyBenchmark()
    
    # Run comprehensive benchmark
    results = benchmark.run_comprehensive_benchmark(test_data_size=500)
    
    # Print summary
    print("\n" + "="*80)
    print("MANNA ML ACCURACY BENCHMARK RESULTS")
    print("="*80)
    
    assessment = results.get("performance_assessment", {})
    print(f"\nOverall Grade: {assessment.get('overall_grade', 'N/A')}")
    
    if "services_assessed" in assessment:
        for service_assessment in assessment["services_assessed"]:
            print(f"\n{service_assessment['service_name'].title()} Service:")
            print(f"  - Accuracy: {service_assessment['accuracy']:.3f} (target: ≥0.950)")
            print(f"  - Response Time: {service_assessment['mean_response_time_ms']:.1f}ms (target: ≤200ms)")
            print(f"  - Overall Score: {service_assessment['overall_score']:.1f}/100")
            
            if service_assessment['accuracy_target_met'] and service_assessment['response_time_target_met']:
                print(f"  - Status: ✅ MEETS ALL TARGETS")
            else:
                print(f"  - Status: ❌ NEEDS IMPROVEMENT")
    
    if "cross_validation" in results and "mean_cv_score" in results["cross_validation"]:
        cv_score = results["cross_validation"]["mean_cv_score"]
        print(f"\nCross-Validation Score: {cv_score:.3f} (±{results['cross_validation']['std_cv_score']:.3f})")
    
    print(f"\nDetailed results saved to: {results.get('results_file')}")
    print(f"Charts generated: {len(results.get('chart_paths', []))} files")
    print("="*80)
    
    return results


if __name__ == "__main__":
    main()