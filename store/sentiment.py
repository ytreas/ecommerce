import json
import re
from collections import Counter
import time
import numpy as np
import sys
import pickle
import joblib

class SentimentNetwork:
    def __init__(self, reviews, labels, min_count=5, polarity_cutoff=0.05, hidden_nodes=20, learning_rate=0.1):
        np.random.seed(1)
        self.pre_process_data(reviews, labels, polarity_cutoff, min_count)
        self.init_network(len(self.review_vocab), hidden_nodes, 1, learning_rate)

    def pre_process_data(self, reviews, labels, polarity_cutoff, min_count):
        positive_counts = Counter()
        negative_counts = Counter()
        total_counts = Counter()

        for i in range(len(reviews)):
            for word in self.preprocess_text(reviews[i]):
                total_counts[word] += 1
                if labels[i] == 'POSITIVE':
                    positive_counts[word] += 1
                else:
                    negative_counts[word] += 1

        pos_neg_ratios = Counter()
        for term, cnt in list(total_counts.most_common()):
            if cnt >= min_count:
                pos_neg_ratio = positive_counts[term] / float(negative_counts[term] + 1)
                pos_neg_ratios[term] = pos_neg_ratio

        for word, ratio in pos_neg_ratios.most_common():
            if ratio > 1:
                pos_neg_ratios[word] = np.log(ratio)
            else:
                pos_neg_ratios[word] = -np.log((1 / (ratio + 0.01)))

        review_vocab = [word for word, ratio in pos_neg_ratios.most_common() 
                        if abs(ratio) >= polarity_cutoff]

        self.review_vocab = list(set(review_vocab))
        self.word2index = {word: i for i, word in enumerate(self.review_vocab)}

    def preprocess_text(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()

    def init_network(self, input_nodes, hidden_nodes, output_nodes, learning_rate):
        self.input_nodes = input_nodes
        self.hidden_nodes = hidden_nodes
        self.output_nodes = output_nodes
        self.learning_rate = learning_rate
        self.weights_0_1 = np.zeros((self.input_nodes, self.hidden_nodes))
        self.weights_1_2 = np.random.normal(0.0, self.output_nodes**-0.5, 
                                            (self.hidden_nodes, self.output_nodes))
        self.layer_1 = np.zeros((1, hidden_nodes))

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -10, 10)))

    def sigmoid_output_2_derivative(self, output):
        return output * (1 - output)

    def train(self, training_reviews, training_labels):
        assert(len(training_reviews) == len(training_labels))

        correct_so_far = 0
        start = time.time()

        for i in range(len(training_reviews)):
            review = training_reviews[i]
            label = training_labels[i]
            
            # Convert review to list of indices
            review_indices = [self.word2index[word] for word in self.preprocess_text(review) if word in self.word2index]
            
            # Forward pass
            self.layer_1 *= 0
            for index in set(review_indices):
                self.layer_1 += self.weights_0_1[index]
            layer_2 = self.sigmoid(self.layer_1.dot(self.weights_1_2))
            
            # Backward pass
            layer_2_error = layer_2 - (1 if label == 'POSITIVE' else 0)
            layer_2_delta = layer_2_error * self.sigmoid_output_2_derivative(layer_2)
            layer_1_error = layer_2_delta.dot(self.weights_1_2.T)
            layer_1_delta = layer_1_error
            
            # Update weights
            self.weights_1_2 -= self.layer_1.T.dot(layer_2_delta) * self.learning_rate
            for index in set(review_indices):
                self.weights_0_1[index] -= layer_1_delta[0] * self.learning_rate
            
            # Track accuracy
            if (layer_2 >= 0.5 and label == 'POSITIVE') or (layer_2 < 0.5 and label == 'NEGATIVE'):
                correct_so_far += 1
            
            # Print progress
            if i % 1000 == 0:
                elapsed_time = float(time.time() - start)
                reviews_per_second = i / elapsed_time if elapsed_time > 0 else 0
                sys.stdout.write(f"\rProgress: {100 * i/float(len(training_reviews)):.2f}% "
                                 f"Speed(reviews/sec): {reviews_per_second:.2f} "
                                 f"#Correct: {correct_so_far} #Trained: {i+1} "
                                 f"Training Accuracy: {correct_so_far * 100 / float(i+1):.2f}%")
                sys.stdout.flush()

        print("\nTraining complete!")

    def test(self, testing_reviews, testing_labels):
        correct = 0
        start = time.time()

        for i in range(len(testing_reviews)):
            pred = self.run(testing_reviews[i])
            if pred == testing_labels[i]:
                correct += 1
            
            if i % 1000 == 0:
                elapsed_time = float(time.time() - start)
                reviews_per_second = i / elapsed_time if elapsed_time > 0 else 0
                sys.stdout.write(f"\rProgress: {100 * i/float(len(testing_reviews)):.2f}% "
                                 f"Speed(reviews/sec): {reviews_per_second:.2f} "
                                 f"#Correct: {correct} #Tested: {i+1} "
                                 f"Testing Accuracy: {correct * 100 / float(i+1):.2f}%")
                sys.stdout.flush()

        print("\nTesting complete!")

    def run(self, review):
        self.layer_1 *= 0
        unique_indices = set()
        for word in self.preprocess_text(review):
            if word in self.word2index:
                unique_indices.add(self.word2index[word])
        for index in unique_indices:
            self.layer_1 += self.weights_0_1[index]
        layer_2 = self.sigmoid(self.layer_1.dot(self.weights_1_2))
        return "POSITIVE" if layer_2[0] >= 0.5 else "NEGATIVE"

def load_data(filename, max_reviews=None):
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if max_reviews and i >= max_reviews:
                break
            try:
                review = json.loads(line)
                text = review.get('text', '')
                rating = review.get('rating', 0)
                
                if not text:
                    continue
                
                label = 'POSITIVE' if float(rating) > 3 else 'NEGATIVE'
                data.append((text, label))
            except json.JSONDecodeError:
                print(f"Error decoding JSON on line {i+1}. Skipping this review.")
            except Exception as e:
                print(f"Error processing review on line {i+1}: {str(e)}. Skipping this review.")
    
    return data

# if __name__ == "__main__":
#     try:
#         max_reviews = 300000  # Increased for better training
#         data = load_data("reviews.jsonl", max_reviews)
#         if not data:
#             raise ValueError("No valid data loaded from the JSONL file.")

#         print(f"Loaded {len(data)} reviews.")

#         # Split data into training and testing sets
#         split = int(0.8 * len(data))
#         train_data, test_data = data[:split], data[split:]

#         train_reviews, train_labels = zip(*train_data)
#         test_reviews, test_labels = zip(*test_data)

#         network = SentimentNetwork(train_reviews, train_labels, min_count=5, polarity_cutoff=0.05, hidden_nodes=20)
        
#         print("Training...")
#         network.train(train_reviews, train_labels)
        
#         print("\nTesting...")
#         network.test(test_reviews, test_labels)
#         while True:
#             user_review = input("\nEnter a review (or 'quit' to exit): ")
#             if user_review.lower() == 'quit':
#                 break
#             sentiment = network.run(user_review)
#             print(f"Sentiment: {sentiment}")

#     except FileNotFoundError:
#         print("Error: The file 'veviews.jsonl' was not found. Please make sure it's in the same directory as this script.")
#     except ValueError as e:
#         print(f"Error: {str(e)}")
#     except Exception as e:
#         print(f"An unexpected error occurred: {str(e)}")
#         import traceback
#         traceback.print_exc()