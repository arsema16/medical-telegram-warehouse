#!/usr/bin/env python3
"""
Simple YOLO detection without matplotlib.
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from ultralytics import YOLO
import cv2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleYOLODetector:
    """Simple YOLO detector without matplotlib."""
    
    IMAGE_CATEGORIES = {
        'promotional': ['person'],
        'product_display': ['bottle', 'cup', 'box', 'package', 'container'],
        'lifestyle': ['person'],
        'other': []
    }
    
    def __init__(self, model_name='yolov8n.pt', conf_threshold=0.25):
        self.model = YOLO(model_name)
        self.conf_threshold = conf_threshold
        self.image_dir = Path("data/raw/images")
        self.output_dir = Path("data/enriched")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def find_images(self):
        """Find images to process."""
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            images.extend(self.image_dir.glob(f"**/{ext}"))
        return images
    
    def classify_image(self, detections):
        """Classify image based on detections."""
        classes = [d['class'] for d in detections]
        has_person = 'person' in classes
        has_product = any(c in classes for c in ['bottle', 'box', 'container', 'package'])
        
        if has_person and has_product:
            return 'promotional'
        elif has_product:
            return 'product_display'
        elif has_person:
            return 'lifestyle'
        return 'other'
    
    def detect_image(self, image_path):
        """Run detection on single image."""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return []
            
            results = self.model(img, conf=self.conf_threshold)
            detections = []
            
            for r in results:
                if r.boxes is not None:
                    for box in r.boxes:
                        class_id = int(box.cls[0])
                        class_name = self.model.names[class_id]
                        confidence = float(box.conf[0])
                        detections.append({
                            'class': class_name,
                            'confidence': confidence
                        })
            return detections
        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}")
            return []
    
    def process_all(self):
        """Process all images."""
        images = self.find_images()
        if not images:
            logger.warning("No images found")
            return []
        
        results = []
        for img_path in images:
            channel = img_path.parent.name
            message_id = int(img_path.stem)
            
            detections = self.detect_image(img_path)
            category = self.classify_image(detections)
            
            result = {
                'message_id': message_id,
                'channel': channel,
                'image_path': str(img_path),
                'category': category,
                'total_detections': len(detections),
                'object_classes': list(set(d['class'] for d in detections))
            }
            results.append(result)
            
        self.save_results(results)
        return results
    
    def save_results(self, results):
        """Save results to CSV and JSON."""
        # Save CSV
        csv_path = self.output_dir / 'yolo_detections.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['message_id', 'channel', 'category', 'total_detections', 'object_classes'])
            for r in results:
                writer.writerow([
                    r['message_id'], r['channel'], r['category'],
                    r['total_detections'], json.dumps(r['object_classes'])
                ])
        
        # Save JSON
        json_path = self.output_dir / 'yolo_detections.json'
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {csv_path} and {json_path}")


def main():
    """Main function."""
    print("=" * 60)
    print("Simple YOLO Detection")
    print("=" * 60)
    
    detector = SimpleYOLODetector()
    results = detector.process_all()
    
    print(f"\n✅ Processed {len(results)} images")
    print(f"📁 Results saved to data/enriched/")

if __name__ == "__main__":
    main()