#!/usr/bin/env python3
"""
Test Runner untuk Sistem Optimasi Logistik.
Menjalankan seluruh unit test dan integration test yang ada pada direktori tests/.
"""
import os
import sys
import unittest

def run_all_tests():
    # Pastikan platform headless aktif sebelum modul PyQt5 di-load
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Tambahkan root proyek ke sys.path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
