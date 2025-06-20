import csv
import os
from collections import Counter

def read_results(file_path="results_history_full.csv", max_results=None):
    """Đọc m kết quả gần nhất từ results_history_full.csv, trả về danh sách màu."""
    colors = []
    try:
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[::-1]  # Đảo ngược để lấy từ mới nhất
            for row in rows[:max_results]:
                color = row.get("color", "").lower()
                if color in ["green", "red"]:
                    colors.append("x" if color == "green" else "d")
                else:
                    print(f"Skipping invalid color: {color}")
            return colors[::-1]
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def generate_patterns(colors, pattern_length):
    """Tạo các mô hình chuỗi dài pattern_length và màu tiếp theo."""
    patterns = []
    if len(colors) < pattern_length + 1:
        print(f"Error: Not enough data. Need at least {pattern_length + 1} results, got {len(colors)}.")
        return patterns
    for i in range(len(colors) - pattern_length):
        pattern = "".join(colors[i:i + pattern_length])
        next_color = colors[i + pattern_length]
        patterns.append(f"{pattern}_{next_color}")
    return patterns

def analyze_patterns(patterns, top_k):
    """Phân tích tần suất mô hình, trả về top k mô hình phổ biến."""
    if not patterns:
        return []
    pattern_counts = Counter(patterns)
    return pattern_counts.most_common(top_k)

def save_patterns(patterns, output_file):
    """Lưu mô hình vào file CSV, trả về đường dẫn file."""
    try:
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Pattern", "Next_Color", "Count"])
            for pattern, count in patterns:
                pattern_parts = pattern.split("_")
                writer.writerow([pattern_parts[0], pattern_parts[1], count])
        return output_file
    except Exception as e:
        print(f"Error saving patterns: {e}")
        return None
