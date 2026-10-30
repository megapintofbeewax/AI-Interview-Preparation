import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.services.tts_service import tts_service, normalize_interview_text, RECOMMENDED_VOICES

class TestTTSService(unittest.TestCase):
    def test_text_normalization(self):
        raw = "Explain how you used `Flask` & REST APIs in your CI/CD pipeline w/ Docker!"
        norm = normalize_interview_text(raw)
        self.assertNotIn("`", norm)
        self.assertIn("A-P-Is", norm)
        self.assertIn("C-I C-D", norm)
        self.assertIn(" and ", norm)
        self.assertTrue(norm.endswith("!"))

    def test_voices_catalog(self):
        voices = tts_service.get_available_voices()
        self.assertGreaterEqual(len(voices), 4)
        voice_ids = [v["id"] for v in voices]
        self.assertIn("en-US-JennyNeural", voice_ids)
        self.assertIn("en-US-GuyNeural", voice_ids)

    def test_synthesize_five_sample_questions(self):
        test_questions = [
            "Tell me about yourself.",
            "Explain the difference between a process and a thread.",
            "Why did you choose Python for your project?",
            "Describe a technical challenge you encountered and how you solved it.",
            "Can you explain that answer in more detail?"
        ]

        async def _run_synthesis():
            results = []
            for q in test_questions:
                audio_path = await tts_service.generate_speech(q)
                self.assertTrue(os.path.exists(audio_path), f"Audio file not found: {audio_path}")
                size = os.path.getsize(audio_path)
                self.assertGreater(size, 4000, f"Audio file size too small: {size} bytes")
                results.append((q, audio_path, size))
            return results

        results = asyncio.run(_run_synthesis())
        for q, path, size in results:
            print(f"[PASS] Synthesized: \"{q}\" -> {path} ({size:,} bytes)")

    def test_caching_performance(self):
        text = "Can you describe your experience with microservices architecture?"

        async def _run_cache_test():
            import time
            # First call (generates or verifies file)
            t0 = time.time()
            p1 = await tts_service.generate_speech(text)
            d1 = time.time() - t0

            # Second call (must be from cache, sub-millisecond)
            t1 = time.time()
            p2 = await tts_service.generate_speech(text)
            d2 = time.time() - t1

            self.assertEqual(p1, p2)
            self.assertLess(d2, 0.05, f"Cache retrieval took too long: {d2}s")
            print(f"[PASS] Cache verified: 1st={d1:.3f}s, 2nd (cache hit)={d2*1000:.2f}ms")

        asyncio.run(_run_cache_test())

if __name__ == "__main__":
    unittest.main()
