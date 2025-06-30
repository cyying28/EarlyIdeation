import os
from pyabsa import available_checkpoints, ABSADatasetList
from pyabsa import AspectTermExtraction as ATEPC

class ABSA:
    @staticmethod
    def analyze_review(review_texts: list[str], max_results: int):
        # Download and load a pretrained ABSA model (ATEPC - Aspect Term Extraction & Polarity Classification)
        checkpoint = "multilingual"
        if checkpoint not in available_checkpoints():
            print(f"Checkpoint '{checkpoint}' not found locally, downloading...")

        # Load pretrained model
        aspect_extractor = ATEPC.AspectTermExtractionCheckpointManager.get_checkpoint(checkpoint).infer(
            [review_text],
            print_result=True,
            save_result=False,
            eval_batch_size=max_results
        )

        return aspect_extractor
    
    @staticmethod
    def format_aspects(aspect_extractor_results):
        """
        Formats the aspect extraction results into a list of dictionaries.
        Each dictionary contains aspect-sentiment pairs for one review.
        """
        review_aspects = []
        
        for result in aspect_extractor_results:
            aspect_sentiments = {}
            for aspect, polarity in zip(result['aspect'], result['sentiment']):
                aspect_sentiments[aspect] = polarity
            review_aspects.append(aspect_sentiments)
        
        return review_aspects

# if __name__ == "__main__":
#     # Example review string
#     review = "The screen is fantastic but the battery life is too short."

#     print(f"\nAnalyzing review:\n{review}\n{'='*40}")

#     result = analyze_review(review)

#     print("\nExtracted Aspects and Sentiments:")
#     for res in result:
#         for aspect, polarity in zip(res['aspect'], res['sentiment']):
#             print(f" - Aspect: \"{aspect}\", Sentiment: {polarity}")