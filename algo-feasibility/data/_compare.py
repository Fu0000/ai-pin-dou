"""Compare A/B/C/D run summaries."""
import json
configs = [
  ('A baseline', 'data/results_a_baseline/summary.json'),
  ('B +bilateral', 'data/results_b_bilateral/summary.json'),
  ('C +bilateral+sat', 'data/results_c_bilateral_sat/summary.json'),
  ('D +bilateral+sat+sharpen', 'data/results_d_full/summary.json'),
]
print(f'{"config":<28}  {"P50":>5}  {"P95":>5}  {"P99":>5}  {"sty_ms":>7}  {"smooth":>7}   cat  face  pet  scene  (median_colors)')
print('-' * 130)
for name, p in configs:
    s = json.load(open(p))
    sty = s['step_p95_ms'].get('stylize', 0)
    cats = s['by_category']
    cc = lambda c: cats.get(c, {}).get('median_colors', '-')
    print(f'{name:<28}  {s["p50_total_s"]:>5.3f}  {s["p95_total_s"]:>5.3f}  {s["p99_total_s"]:>5.3f}  {sty:>7}  {s["median_smoothness_lab"]:>7}    {cc("cat"):>3}   {cc("face"):>3}  {cc("pet"):>3}    {cc("scene"):>3}')
print()
print('Per-category smoothness (smaller = neighbors more similar = visually smoother):')
print(f'{"config":<28}  {"cat":>6}  {"face":>6}  {"pet":>6}  {"scene":>6}')
print('-' * 70)
for name, p in configs:
    s = json.load(open(p))
    cats = s['by_category']
    print(f'{name:<28}  {cats["cat"]["median_smoothness_lab"]:>6}  {cats["face"]["median_smoothness_lab"]:>6}  {cats["pet"]["median_smoothness_lab"]:>6}  {cats["scene"]["median_smoothness_lab"]:>6}')
print()
print('Per-category P95 (s):')
print(f'{"config":<28}  {"cat":>6}  {"face":>6}  {"pet":>6}  {"scene":>6}')
print('-' * 70)
for name, p in configs:
    s = json.load(open(p))
    cats = s['by_category']
    print(f'{name:<28}  {cats["cat"]["p95_s"]:>6.3f}  {cats["face"]["p95_s"]:>6.3f}  {cats["pet"]["p95_s"]:>6.3f}  {cats["scene"]["p95_s"]:>6.3f}')
