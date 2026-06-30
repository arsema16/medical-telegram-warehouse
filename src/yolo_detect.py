#!/usr/bin/env python3
"""
YOLOv8 Object Detection for Telegram Images
Enriches message data with image classification results.
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import sqlite3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YOLODetector:
    """
    YOLOv8 object detector for Telegram images.
    """
    
    # Classification scheme based on detected objects
    IMAGE_CATEGORIES = {
        'promotional': ['person', 'hand', 'arm'],  # Person showing product
        'product_display': ['bottle', 'cup', 'box', 'package', 'container', 'pill', 'capsule'],
        'lifestyle': ['person'],  # Person, no product
        'other': []  # Neither
    }
    
    # Common medical/pharmacy related objects
    MEDICAL_OBJECTS = ['pill', 'capsule', 'tablet', 'bottle', 'syringe', 'bandage', 'glove', 'mask']
    
    def __init__(self, model_name: str = 'yolov8n.pt', confidence_threshold: float = 0.25):
        """
        Initialize YOLO detector.
        
        Args:
            model_name: YOLO model name (yolov8n.pt, yolov8s.pt, etc.)
            confidence_threshold: Minimum confidence score for detections
        """
        self.model = YOLO(model_name)
        self.confidence_threshold = confidence_threshold
        self.image_dir = Path("data/raw/images")
        self.output_dir = Path("data/enriched")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Results storage
        self.detections = []
        self.image_categories = {}
        self.medical_detections = []
        
        logger.info(f"YOLO Detector initialized with model: {model_name}")
        logger.info(f"Confidence threshold: {confidence_threshold}")
    
    def find_images(self) -> List[Path]:
        """
        Find all images in the data lake.
        
        Returns:
            List of image file paths
        """
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']:
            images.extend(self.image_dir.glob(f"**/{ext}"))
        logger.info(f"Found {len(images)} images")
        return images
    
    def classify_image(self, detections: List[Dict]) -> str:
        """
        Classify image based on detected objects.
        
        Args:
            detections: List of detected objects with class names
            
        Returns:
            Category string: 'promotional', 'product_display', 'lifestyle', or 'other'
        """
        detected_classes = [d['class'] for d in detections]
        
        # Check for promotional (person + product)
        has_person = 'person' in detected_classes
        has_product = any(obj in detected_classes for obj in ['bottle', 'box', 'package', 'container'])
        
        if has_person and has_product:
            return 'promotional'
        elif has_product:
            return 'product_display'
        elif has_person:
            return 'lifestyle'
        else:
            return 'other'
    
    def contains_medical_objects(self, detections: List[Dict]) -> bool:
        """
        Check if detections include medical/pharmaceutical objects.
        
        Args:
            detections: List of detected objects
            
        Returns:
            True if medical objects detected
        """
        detected_classes = [d['class'] for d in detections]
        return any(obj in detected_classes for obj in self.MEDICAL_OBJECTS)
    
    def detect_image(self, image_path: Path) -> List[Dict]:
        """
        Run YOLO detection on a single image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detection dictionaries
        """
        try:
            # Load image
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning(f"Failed to load image: {image_path}")
                return []
            
            # Run inference
            results = self.model(img, conf=self.confidence_threshold)
            
            detections = []
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class name and confidence
                        class_id = int(box.cls[0])
                        class_name = self.model.names[class_id]
                        confidence = float(box.conf[0])
                        
                        detections.append({
                            'class_id': class_id,
                            'class': class_name,
                            'confidence': confidence,
                            'bbox': box.xyxy[0].tolist()
                        })
            
            return detections
            
        except Exception as e:
            logger.error(f"Error detecting objects in {image_path}: {e}")
            return []
    
    def process_image(self, image_path: Path) -> Dict[str, Any]:
        """
        Process a single image: detect objects and classify.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with detection results
        """
        # Extract message_id from filename or path
        # Assumes format: channel_name/message_id.jpg
        channel = image_path.parent.name
        message_id = int(image_path.stem)
        
        # Run detection
        detections = self.detect_image(image_path)
        
        # Classify image
        category = self.classify_image(detections)
        is_medical = self.contains_medical_objects(detections)
        
        # Count objects by class
        object_counts = defaultdict(int)
        for d in detections:
            object_counts[d['class']] += 1
        
        # Get top detected objects
        top_objects = sorted(detections, key=lambda x: x['confidence'], reverse=True)[:5]
        
        result = {
            'image_path': str(image_path),
            'channel': channel,
            'message_id': message_id,
            'category': category,
            'is_medical': is_medical,
            'object_counts': dict(object_counts),
            'top_objects': top_objects,
            'total_detections': len(detections),
            'detections': detections
        }
        
        return result
    
    def process_all_images(self) -> List[Dict]:
        """
        Process all images in the data lake.
        
        Returns:
            List of detection results
        """
        images = self.find_images()
        
        if not images:
            logger.warning("No images found to process")
            return []
        
        results = []
        for i, img_path in enumerate(images):
            logger.info(f"Processing {i+1}/{len(images)}: {img_path}")
            result = self.process_image(img_path)
            results.append(result)
        
        # Save results
        self.save_results(results)
        
        return results
    
    def save_results(self, results: List[Dict]) -> None:
        """
        Save detection results to CSV and JSON.
        
        Args:
            results: List of detection results
        """
        # Save as CSV
        csv_path = self.output_dir / 'yolo_detections.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'message_id', 'channel', 'image_path', 'category',
                'is_medical', 'total_detections', 'object_counts',
                'top_objects_json'
            ])
            
            for r in results:
                writer.writerow([
                    r['message_id'],
                    r['channel'],
                    r['image_path'],
                    r['category'],
                    r['is_medical'],
                    r['total_detections'],
                    json.dumps(r['object_counts']),
                    json.dumps(r['top_objects'])
                ])
        
        logger.info(f"Results saved to CSV: {csv_path}")
        
        # Save as JSON (detailed)
        json_path = self.output_dir / 'yolo_detections.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to JSON: {json_path}")
        
        # Generate summary
        self.generate_summary(results)
    
    def generate_summary(self, results: List[Dict]) -> None:
        """
        Generate summary statistics from detection results.
        
        Args:
            results: List of detection results
        """
        # Count by category
        category_counts = defaultdict(int)
        medical_count = 0
        total_detections = 0
        
        for r in results:
            category_counts[r['category']] += 1
            if r['is_medical']:
                medical_count += 1
            total_detections += r['total_detections']
        
        summary = {
            'total_images_processed': len(results),
            'categories': dict(category_counts),
            'medical_images': medical_count,
            'total_detections': total_detections,
            'avg_detections_per_image': total_detections / len(results) if results else 0
        }
        
        # Save summary
        summary_path = self.output_dir / 'yolo_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary saved to: {summary_path}")
        logger.info(f"Category distribution: {dict(category_counts)}")
    
    def load_to_database(self, db_path: str = "data/warehouse.db") -> None:
        """
        Load detection results to database.
        
        Args:
            db_path: Path to SQLite database
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create detections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fct_image_detections (
                detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                channel_name TEXT,
                image_path TEXT,
                category TEXT,
                is_medical INTEGER DEFAULT 0,
                total_detections INTEGER DEFAULT 0,
                object_counts TEXT,
                top_objects TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages(message_id)
            )
        """)
        
        # Load results
        results_file = self.output_dir / 'yolo_detections.json'
        if not results_file.exists():
            logger.warning("No results file found. Run detection first.")
            conn.close()
            return
        
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        loaded = 0
        for r in results:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO fct_image_detections (
                        message_id, channel_name, image_path,
                        category, is_medical, total_detections,
                        object_counts, top_objects
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r['message_id'],
                    r['channel'],
                    r['image_path'],
                    r['category'],
                    1 if r['is_medical'] else 0,
                    r['total_detections'],
                    json.dumps(r['object_counts']),
                    json.dumps(r['top_objects'])
                ))
                loaded += 1
            except Exception as e:
                logger.error(f"Failed to load detection for message {r['message_id']}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Loaded {loaded} detections to database")

def main():
    """Main entry point."""
    print("=" * 60)
    print("YOLO Object Detection")
    print("=" * 60)
    
    # Initialize detector
    detector = YOLODetector(model_name='yolov8n.pt')
    
    # Process all images
    results = detector.process_all_images()
    
    if results:
        print(f"\n✅ Processed {len(results)} images")
        print(f"📊 Results saved to: {detector.output_dir}")
        
        # Load to database
        detector.load_to_database()
    else:
        print("\n⚠️ No images found to process")
        print("Please run the scraper first to download images.")

if __name__ == "__main__":
    main()