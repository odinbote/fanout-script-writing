"""Offline tests. ScrapeCreators fixtures are the sample responses from its public OpenAPI docs.
Run: /opt/homebrew/bin/python3.14 -m unittest discover -s tests -v   (from the project root)"""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import checks, rank, store  # noqa: E402
from pipeline.sources import amazon, meta_connector  # noqa: E402
from pipeline.sources import scrapecreators as sc  # noqa: E402

FX = ROOT / "tests" / "fixtures" / "sc"


def fx(name):
    return json.loads((FX / f"{name}.json").read_text())


class ScrapeCreatorsNormalizers(unittest.TestCase):
    def test_fb_company_ads(self):
        it = sc.norm_fb_ad(fx("fb_company_ads")["results"][0], query="competitor:Nike", now_ts=1750300000)
        self.assertEqual(it["pillar"], "ads")
        self.assertTrue(it["id"].startswith("meta_ads:"))
        self.assertEqual(it["author"], "Nike")
        self.assertTrue(it["text"])
        self.assertEqual(it["metrics"]["days_active"], (1750300000 - 1750143600) // 86400)

    def test_fb_search_ads(self):
        it = sc.norm_fb_ad(fx("fb_search_ads")["searchResults"][0])
        self.assertTrue(it["text"])

    def test_fb_ad_detail(self):
        d = sc.norm_fb_ad_detail(fx("fb_ad"))
        self.assertTrue(d["text"])

    def test_tiktok(self):
        it = sc.norm_tiktok(fx("tiktok_search")["search_item_list"][0])
        self.assertGreater(it["metrics"]["views"], 0)
        self.assertTrue(it["author"])
        self.assertIn("tiktok.com", it["url"])

    def test_tiktok_transcript_vtt(self):
        self.assertTrue(sc.vtt_to_text(fx("tiktok_transcript")["transcript"]).startswith("Alright"))

    def test_instagram(self):
        r = sc.norm_ig_reel_search(fx("ig_reels_search")["reels"][0])
        self.assertTrue(r["author"])
        u = sc.norm_ig_user_reel(fx("ig_user_reels")["items"][0])
        self.assertGreater(u["metrics"]["views"], 0)
        self.assertTrue(u["text"])

    def test_youtube(self):
        it = sc.norm_yt(fx("yt_channel_shorts")["shorts"][0])
        self.assertEqual(it["metrics"]["views"], 17066)
        it = sc.norm_yt(fx("yt_search")["videos"][0])
        self.assertTrue(it["author"])

    def test_reddit(self):
        it = sc.norm_reddit(fx("reddit_search")["posts"][0])
        self.assertGreater(it["metrics"]["score"], 0)
        it = sc.norm_reddit(fx("reddit_subreddit")["posts"][0])
        self.assertIn("/comments/", it["url"])
        self.assertTrue(sc.norm_reddit_comments(fx("reddit_comments")))

    def test_linkedin_and_x(self):
        li = sc.norm_linkedin(fx("linkedin_search")["posts"][0])
        self.assertEqual(li["source"], "linkedin")
        self.assertTrue(li["text"])
        tw = sc.norm_tweet(fx("twitter_search")["posts"][0])
        self.assertEqual(tw["author"], "code_rams")
        self.assertEqual(tw["metrics"]["likes"], 11)


class ConnectorImport(unittest.TestCase):
    def test_raw_tool_result(self):
        blob = {"query": "system design interview", "status": "ACTIVE", "results": json.dumps({"ads": [
            {"id": "1", "page_id": 9, "page_name": "Acme Learning", "ad_creative_link_title": "Get smarter",
             "ad_delivery_start_time": 1790000000, "ad_snapshot_url": "https://www.facebook.com/ads/library/?id=1"}]})}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(blob, f)
        items = meta_connector.load_file(f.name)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "meta_ads:1")
        self.assertTrue(items[0]["metrics"]["is_active"])
        self.assertGreater(items[0]["metrics"]["days_active"], 0)


class AdLibraryPage(unittest.TestCase):
    TEXT = """URL: https://www.facebook.com/ads/library/?view_all_page_id=42
~450 results
Active
Library ID: 111
Started running on 24 Nov 2024
Platforms
​
See ad details
Brand
Sponsored
Line one of the copy.

Line two.
BLOG.EXAMPLE.COM
Brand
Learn more
​
Inactive
Library ID: 222
13 Aug 2026 - 9 Oct 2026
This ad has multiple versions
3 ads use this creative and text
Brand
Sponsored
The #1 newsletter for system design.
0:00 / 0:50
Get smarter on system design
Join for FREE Today!
Subscribe
​
Active
Library ID: 333
Started running on 9 Oct 2026
Brand
Sponsored
Short copy here.
Get smarter on system design
Join for FREE Today!
Subscribe
See more
System status
"""

    def test_parse(self):
        from pipeline.sources import adlibrary_page
        now = 1794390000  # 2026-11-11
        a, b, c = adlibrary_page.parse(self.TEXT, now_ts=now)
        self.assertEqual(a["extra"]["page_id"], "42")
        self.assertTrue(a["metrics"]["is_active"])
        self.assertEqual(a["text"], "Line one of the copy.\n\nLine two.")
        self.assertEqual(a["extra"]["cta"], "Learn more")
        self.assertFalse(b["metrics"]["is_active"])
        self.assertEqual(b["metrics"]["days_active"], 57)
        self.assertEqual(b["metrics"]["variants_listed"], 3)
        self.assertEqual(b["metrics"]["video_s"], 50)
        self.assertEqual(b["title"], "Get smarter on system design")
        self.assertEqual(c["text"], "Short copy here.")
        self.assertEqual(c["extra"]["cta"], "Subscribe")


class Ranking(unittest.TestCase):
    def test_ads_variants_and_grades(self):
        base = dict(metrics={"days_active": 70, "is_active": True}, extra={"page_id": "9"}, text="Same body")
        items = [store.make_item("ads", "meta_ads", str(i), **base) for i in range(3)]
        items.append(store.make_item("ads", "meta_ads", "x", metrics={"days_active": 3, "is_active": True},
                                     extra={"page_id": "9"}, text="Other"))
        rows = {i: (s, g) for i, s, g in rank.score_ads(items)}
        self.assertIn("Long-Runner", rows["meta_ads:0"][1])
        self.assertIn("3 variants", rows["meta_ads:0"][1])
        self.assertGreater(rows["meta_ads:0"][0], rows["meta_ads:x"][0])

    def test_organic_outlier(self):
        items = [store.make_item("organic", "youtube", str(i), author="C", metrics={"views": 1000}) for i in range(6)]
        items.append(store.make_item("organic", "youtube", "hit", author="C", metrics={"views": 50000}))
        rows = {i: (s, g) for i, s, g in rank.score_organic(items)}
        self.assertIn("Mega outlier", rows["youtube:hit"][1])


class Checks(unittest.TestCase):
    def test_overlap(self):
        o = checks.overlap("I was stuck in tutorial hell for two whole years until this", "stuck in tutorial hell for two whole years")
        self.assertGreater(o["copied_share"], 0.5)
        self.assertEqual(checks.overlap("totally different words here now", "nothing alike at all ok")["runs"], [])

    def test_clip_plan(self):
        p = checks.clip_plan("This is basically a cheat code for engineers. If you want to start thinking like a senior engineer, check out Fanout.sh.")
        self.assertEqual(len(p["clips"]), 2)
        self.assertEqual(p["clips"][0]["seconds"], 4)


class PastedAmazon(unittest.TestCase):
    def test_parse(self):
        text = """Priya
5.0 out of 5 stars Finally understood consistent hashing
Reviewed in the United States on March 3, 2026
Format: Paperback Verified Purchase
The diagrams made it click. I wish it had more on real production failures.
21 people found this helpful
Helpful Report
Sam K
2.0 out of 5 stars Too shallow for senior roles
Reviewed in India on May 1, 2026
Reads like a cheat sheet. No depth on trade-offs.
One person found this helpful
"""
        items = amazon.parse_pasted_reviews(text, "SDI vol 1")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["metrics"], {"rating": 5.0, "helpful": 21})
        self.assertIn("diagrams", items[0]["text"])
        self.assertNotIn("Sam K", items[0]["text"])
        self.assertEqual(items[1]["metrics"]["helpful"], 1)


if __name__ == "__main__":
    unittest.main()
