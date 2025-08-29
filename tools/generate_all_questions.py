#!/usr/bin/env python3
"""
Generate Questions for All Documents

Script to process all documents in all_documents.json and generate trivia questions
using the appropriate prompts for each document type (god, ability, patch, god_change, item).
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from question_generation.smite_generator import SmiteQuestionGenerator
from question_generation.models import QuestionBank
from llm.client import LLMClient
from llm.config import get_question_generation_config


class BatchQuestionGenerator:
    """Handles batch generation of questions for all Smite documents."""
    
    def __init__(self, 
                 data_file: str = None,
                 output_dir: str = "generated_questions",
                 questions_per_doc: int = 1,
                 question_type: str = "multiple_choice",
                 difficulty: str = "medium",
                 batch_size: int = 50,
                 delay_between_batches: float = 2.0):
        """
        Initialize batch question generator.
        
        Args:
            data_file: Path to all_documents.json file
            output_dir: Directory to save generated questions
            questions_per_doc: Number of questions per document
            question_type: Type of questions to generate
            difficulty: Question difficulty level
            batch_size: Number of documents to process in each batch
            delay_between_batches: Delay in seconds between batches
        """
        self.data_file = data_file or "data/smite/all_documents.json"
        self.output_dir = Path(output_dir)
        self.questions_per_doc = questions_per_doc
        self.question_type = question_type
        self.difficulty = difficulty
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            "total_documents": 0,
            "processed_documents": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "skipped_documents": 0,  # LLM decided not suitable for trivia
            "total_questions_generated": 0,
            "questions_by_type": {},
            "skipped_by_type": {},  # Track skips by document type
            "errors": []
        }
        
        # Initialize LLM client and generator
        self.llm_client = None
        self.generator = None
    
    def initialize_llm(self) -> bool:
        """Initialize LLM client and question generator."""
        try:
            config = get_question_generation_config()
            self.llm_client = LLMClient(config)
            
            # Test LLM connection
            if not self.llm_client.health_check():
                print("❌ LLM service not available")
                print("   Make sure Ollama is running: ollama serve")
                print("   And granite3.2:8b is installed: ollama pull granite3.2:8b")
                return False
            
            print("✅ LLM service is healthy")
            
            # Initialize question generator
            self.generator = SmiteQuestionGenerator(
                data_file_path=self.data_file,
                llm_client=self.llm_client
            )
            
            # Load data and prompts
            if not self.generator.load_data():
                print("❌ Failed to load Smite data")
                return False
            
            if not self.generator.load_prompts():
                print("❌ Failed to load prompts")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize LLM: {e}")
            return False
    
    def load_documents(self) -> List[Dict[str, Any]]:
        """Load all documents from the JSON file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            self.stats["total_documents"] = len(documents)
            print(f"📊 Loaded {len(documents)} documents")
            
            # Count documents by type
            type_counts = {}
            for doc in documents:
                doc_type = doc.get('type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            print("Document types:")
            for doc_type, count in sorted(type_counts.items()):
                print(f"  - {doc_type}: {count} documents")
            
            return documents
            
        except Exception as e:
            print(f"❌ Error loading documents: {e}")
            return []
    
    def process_document(self, document: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Process a single document and generate questions."""
        try:
            doc_name = document.get('name', 'Unknown')
            doc_type = document.get('type', 'unknown')
            
            # Generate questions for this document
            questions = self.generator.generate_questions_for_document(
                document=document,
                question_type=self.question_type,
                count=self.questions_per_doc,
                difficulty=self.difficulty
            )
            
            if questions:
                self.stats["successful_generations"] += 1
                self.stats["total_questions_generated"] += len(questions)
                
                # Track questions by document type
                if doc_type not in self.stats["questions_by_type"]:
                    self.stats["questions_by_type"][doc_type] = 0
                self.stats["questions_by_type"][doc_type] += len(questions)
                
                return questions
            else:
                # Check if this was an intentional skip (empty response) vs failure
                # Empty questions list could mean LLM decided document wasn't suitable for trivia
                # This is different from an error/failure
                self.stats["skipped_documents"] += 1
                
                # Track skips by document type
                if doc_type not in self.stats["skipped_by_type"]:
                    self.stats["skipped_by_type"][doc_type] = 0
                self.stats["skipped_by_type"][doc_type] += 1
                
                # Don't treat this as an error since it's a valid decision by the LLM
                return []
                
        except Exception as e:
            self.stats["failed_generations"] += 1
            error_msg = f"Error processing {document.get('type', 'unknown')}: {document.get('name', 'Unknown')} - {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return None
    
    def process_batch(self, documents: List[Dict[str, Any]], start_idx: int) -> Dict[str, List[Dict[str, Any]]]:
        """Process a batch of documents."""
        batch_end = min(start_idx + self.batch_size, len(documents))
        batch_documents = documents[start_idx:batch_end]
        
        print(f"\n📝 Processing batch {start_idx//self.batch_size + 1}: documents {start_idx+1}-{batch_end}")
        print("=" * 60)
        
        # Group questions by document type for organized output
        questions_by_type = {}
        
        for i, document in enumerate(batch_documents, start_idx + 1):
            doc_name = document.get('name', 'Unknown')
            doc_type = document.get('type', 'unknown')
            
            print(f"🔍 {i:3d}/{len(documents)} - Processing {doc_type}: {doc_name}")
            
            questions = self.process_document(document)
            
            if questions:
                if doc_type not in questions_by_type:
                    questions_by_type[doc_type] = []
                
                # Add source document metadata to each question
                for question in questions:
                    question['metadata'] = question.get('metadata', {})
                    question['metadata'].update({
                        'source_document_id': document.get('id', ''),
                        'source_document_name': doc_name,
                        'source_document_type': doc_type,
                        'generated_at': datetime.now().isoformat(),
                        'generator_version': '1.0.0'
                    })
                
                questions_by_type[doc_type].extend(questions)
                print(f"   ✅ Generated {len(questions)} questions")
            elif isinstance(questions, list) and len(questions) == 0:
                # Empty list means LLM intentionally skipped (not suitable for trivia)
                print(f"   📝 Skipped (not suitable for trivia)")
            else:
                print(f"   ❌ Failed to generate questions")
            
            self.stats["processed_documents"] += 1
        
        return questions_by_type
    
    def save_questions(self, all_questions: Dict[str, List[Dict[str, Any]]], batch_num: int = None):
        """Save generated questions to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for doc_type, questions in all_questions.items():
            if not questions:
                continue
            
            # Create question bank
            suffix = f"_batch{batch_num}" if batch_num is not None else ""
            bank_name = f"smite_{doc_type}_generated_{timestamp}{suffix}"
            
            question_bank = QuestionBank(
                bank_name=bank_name,
                source_type="smite_auto_generated",
                description=f"Auto-generated {self.question_type} questions from Smite {doc_type} data using granite3.2:8b LLM",
                questions=questions
            )
            
            # Save as JSON file
            filename = f"{bank_name}.json"
            output_file = self.output_dir / filename
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(question_bank.model_dump(), f, indent=2, ensure_ascii=False)
                
                print(f"💾 Saved {len(questions)} {doc_type} questions to {output_file}")
                
            except Exception as e:
                error_msg = f"Failed to save {doc_type} questions: {e}"
                self.stats["errors"].append(error_msg)
                print(f"❌ {error_msg}")
    
    def print_progress_stats(self, batch_num: int, total_batches: int):
        """Print progress statistics."""
        processed = self.stats["processed_documents"]
        total = self.stats["total_documents"]
        success_rate = (self.stats["successful_generations"] / max(processed, 1)) * 100
        
        print(f"\n📊 Progress Report - Batch {batch_num}/{total_batches}")
        print("=" * 50)
        print(f"Documents processed: {processed}/{total} ({(processed/total)*100:.1f}%)")
        print(f"Successful generations: {self.stats['successful_generations']}")
        print(f"Skipped documents: {self.stats['skipped_documents']} (LLM decided not suitable)")
        print(f"Failed generations: {self.stats['failed_generations']}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Total questions generated: {self.stats['total_questions_generated']}")
        
        if self.stats["questions_by_type"]:
            print("\nQuestions by document type:")
            for doc_type, count in sorted(self.stats["questions_by_type"].items()):
                print(f"  - {doc_type}: {count} questions")
        
        if self.stats["skipped_by_type"]:
            print("\nSkipped documents by type:")
            for doc_type, count in sorted(self.stats["skipped_by_type"].items()):
                print(f"  - {doc_type}: {count} skipped")
    
    def generate_all_questions(self, 
                             limit: Optional[int] = None,
                             document_types: Optional[List[str]] = None,
                             save_batches: bool = True) -> bool:
        """
        Generate questions for all documents.
        
        Args:
            limit: Maximum number of documents to process (None for all)
            document_types: Filter by document types (None for all types)
            save_batches: Whether to save questions after each batch
            
        Returns:
            True if successful, False otherwise
        """
        print("🚀 Starting batch question generation")
        print(f"⚙️  Configuration:")
        print(f"   - Questions per document: {self.questions_per_doc}")
        print(f"   - Question type: {self.question_type}")
        print(f"   - Difficulty: {self.difficulty}")
        print(f"   - Batch size: {self.batch_size}")
        print(f"   - Delay between batches: {self.delay_between_batches}s")
        print(f"   - Output directory: {self.output_dir}")
        
        # Initialize LLM
        if not self.initialize_llm():
            return False
        
        # Load documents
        documents = self.load_documents()
        if not documents:
            return False
        
        # Filter by document types if specified
        if document_types:
            documents = [doc for doc in documents if doc.get('type') in document_types]
            print(f"📋 Filtered to {len(documents)} documents of types: {document_types}")
        
        # Apply limit if specified
        if limit:
            documents = documents[:limit]
            print(f"📋 Limited to first {len(documents)} documents")
        
        # Calculate batches
        total_batches = (len(documents) + self.batch_size - 1) // self.batch_size
        print(f"📦 Will process {len(documents)} documents in {total_batches} batches")
        
        all_questions = {}
        start_time = time.time()
        
        try:
            # Process documents in batches
            for batch_num in range(total_batches):
                batch_start = batch_num * self.batch_size
                
                # Process this batch
                batch_questions = self.process_batch(documents, batch_start)
                
                # Merge batch questions into all_questions
                for doc_type, questions in batch_questions.items():
                    if doc_type not in all_questions:
                        all_questions[doc_type] = []
                    all_questions[doc_type].extend(questions)
                
                # Save batch if requested
                if save_batches and batch_questions:
                    self.save_questions(batch_questions, batch_num + 1)
                
                # Print progress
                self.print_progress_stats(batch_num + 1, total_batches)
                
                # Delay between batches (except for the last one)
                if batch_num < total_batches - 1 and self.delay_between_batches > 0:
                    print(f"⏳ Waiting {self.delay_between_batches}s before next batch...")
                    time.sleep(self.delay_between_batches)
            
            # Save final combined results if not saving batches
            if not save_batches:
                self.save_questions(all_questions)
            
            # Final statistics
            elapsed_time = time.time() - start_time
            print(f"\n🎉 Generation Complete!")
            print("=" * 50)
            print(f"Total time: {elapsed_time:.1f} seconds")
            print(f"Average time per document: {elapsed_time/max(self.stats['processed_documents'], 1):.2f}s")
            print(f"Total questions generated: {self.stats['total_questions_generated']}")
            
            if self.stats["errors"]:
                print(f"\n⚠️  {len(self.stats['errors'])} errors occurred:")
                for error in self.stats["errors"][-10:]:  # Show last 10 errors
                    print(f"   - {error}")
                if len(self.stats["errors"]) > 10:
                    print(f"   ... and {len(self.stats['errors']) - 10} more errors")
            
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️  Generation interrupted by user")
            if all_questions:
                print("💾 Saving partial results...")
                self.save_questions(all_questions)
            return False
        except Exception as e:
            print(f"\n❌ Generation failed: {e}")
            return False


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Generate trivia questions for all Smite documents")
    
    parser.add_argument("--data-file", type=str, 
                       default="data/smite/all_documents.json",
                       help="Path to all_documents.json file")
    
    parser.add_argument("--output-dir", type=str,
                       default="generated_questions",
                       help="Output directory for generated questions")
    
    parser.add_argument("--questions-per-doc", type=int, default=1,
                       help="Number of questions to generate per document")
    
    parser.add_argument("--question-type", type=str, default="multiple_choice",
                       choices=["multiple_choice", "true_false", "open_ended"],
                       help="Type of questions to generate")
    
    parser.add_argument("--difficulty", type=str, default="medium",
                       choices=["easy", "medium", "hard"],
                       help="Question difficulty level")
    
    parser.add_argument("--batch-size", type=int, default=50,
                       help="Number of documents to process in each batch")
    
    parser.add_argument("--delay", type=float, default=2.0,
                       help="Delay in seconds between batches")
    
    parser.add_argument("--limit", type=int, default=None,
                       help="Maximum number of documents to process")
    
    parser.add_argument("--types", type=str, nargs="+",
                       choices=["god", "ability", "patch", "god_change", "item"],
                       help="Filter by document types")
    
    parser.add_argument("--no-batch-save", action="store_true",
                       help="Don't save after each batch (only save final result)")
    
    args = parser.parse_args()
    
    # Create batch generator
    generator = BatchQuestionGenerator(
        data_file=args.data_file,
        output_dir=args.output_dir,
        questions_per_doc=args.questions_per_doc,
        question_type=args.question_type,
        difficulty=args.difficulty,
        batch_size=args.batch_size,
        delay_between_batches=args.delay
    )
    
    # Generate questions
    success = generator.generate_all_questions(
        limit=args.limit,
        document_types=args.types,
        save_batches=not args.no_batch_save
    )
    
    if success:
        print(f"\n✅ Questions saved to: {generator.output_dir}")
        exit(0)
    else:
        print(f"\n❌ Generation failed or was interrupted")
        exit(1)


if __name__ == "__main__":
    main()