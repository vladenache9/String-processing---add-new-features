import sys
import os
import ahocorasick
import time
import hashlib
import json


class FileHandler:

    def __init__(self, file_path):
        if not os.path.isfile(file_path):
            raise ValueError(f"The path {file_path} is not a valid file.")
        self.file_path = file_path

    def read_file(self, buffer_size=1024 * 1024):
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                yield data

    def compute_hash(self):
        hasher = hashlib.sha256()
        for data in self.read_file():
            hasher.update(data.encode('utf-8'))
        return hasher.hexdigest()


class SequenceSearcher:

    def __init__(self, patterns):
        self.patterns = patterns
        self.automaton = ahocorasick.Automaton(ahocorasick.STORE_INTS)
        self.occurrences = {pattern: 0 for pattern in patterns}
        self._build_automaton()

    def _build_automaton(self):
        for idx, pattern in enumerate(self.patterns):
            self.automaton.add_word(pattern, idx)
        self.automaton.make_automaton()

    def search_in_data(self, data):
        for end_index, insert_order in self.automaton.iter_long(data):
            original_value = self.patterns[insert_order]
            self.occurrences[original_value] += 1

    def get_results(self):
        return self.occurrences


class ResultDisplayer:

    @staticmethod
    def display_results(occurrences):
        for pattern, count in occurrences.items():
            print(f'{pattern} : {count} occurrences!')

    @staticmethod
    def display_execution_time(start_time):
        print(f"\nreal    {time.time() - start_time:.3f}s")


class PersistentStorage:

    def __init__(self, storage_file='results.json'):
        self.storage_file = storage_file
        self.storage = self._load_storage()

    def _load_storage(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        return {}

    def save_storage(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.storage, f, indent=4)

    def get_results(self, file_hash):
        return self.storage.get(file_hash, None)

    def store_results(self, file_hash, results):
        self.storage[file_hash] = results


class CommandLineInterface:
    @staticmethod
    def get_input():
        file_path = sys.argv[1]
        patterns = sys.argv[2:]
        return file_path, patterns

    @staticmethod
    def run():
        file_path, patterns = CommandLineInterface.get_input()
        start_time = time.time()

        try:
            file_handler = FileHandler(file_path)
            file_hash = file_handler.compute_hash()

            storage = PersistentStorage()
            results = storage.get_results(file_hash)

            if results:
                print(f"File {file_path} already processed. Retrieved results from storage.")
            else:
                searcher = SequenceSearcher(patterns)
                for data in file_handler.read_file():
                    searcher.search_in_data(data)

                results = searcher.get_results()
                storage.store_results(file_hash, results)
                storage.save_storage()

            ResultDisplayer.display_results(results)
            ResultDisplayer.display_execution_time(start_time)

        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    CommandLineInterface.run()
