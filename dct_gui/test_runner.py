class TestRunner:
    def __init__(self, serial_manager=None):
        """Initialize the TestRunner.
        Args:
            serial_manager (SerialManager, optional): An instance of SerialManager for handling serial communication.
                Defaults to None."""
        
        self.serial = serial_manager
        self.test_definition = None
    
    def load_test(self, test_data):
        """ Store the loaded YAML test data."""
        
        self.test_definition = test_data
    
    def run_test(self):
        """
        Simulate running the test.
        For now, just create dummy pass/fail results.
        Returns:
            List of strings describing results.
        """
        if not self.test_definition:
            return ["No test loaded."]
        
        results = []
        truth_table = self.test_definition.get('truth_table', [])

        for i, row in enumerate(truth_table):
            # Simulate "PASS" for all rows for now
            inputs = row.get('inputs')
            expected = row.get('ouput')
            results.append(f"Test {i+1}: Inputs {inputs} => Expected {expected} => Result: PASS")
        return results
    
    def format_results(self, results):
        """
        Format the test results for display.
        Args:
            results (list): List of result strings.
        Returns:
            str: Formatted string of results.
        """
        return "\n".join(results)