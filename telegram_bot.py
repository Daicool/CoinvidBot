import os
import csv
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from pattern_analyzer import read_results, generate_patterns, analyze_patterns, save_patterns
from key_manager import create_key, is_key_valid, list_keys, delete_key

# Cấu hình logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Trạng thái hội thoại
PATTERN_LENGTH, TOP_K, MAX_RESULTS = range(3)

# Đọc biến môi trường
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Lưu key tạm thời cho người dùng
USER_KEYS = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start."""
    user_id = update.effective_user.id
    contact_msg = "\nLiên hệ @Nhanoke để mua key và sử dụng."
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "Chào admin! Dùng /admin để quản lý, /analyze để phân tích, hoặc /help để xem hướng dẫn." + contact_msg
        )
    else:
        await update.message.reply_text(
            "Chào mừng bạn! Vui lòng nhập key bằng /set_key <key> để sử dụng bot. Xem /help để biết thêm." + contact_msg
        )

async def set_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /set_key."""
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("Admin không cần key. Dùng /analyze hoặc /admin.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Vui lòng nhập key. Ví dụ: /set_key ABC123XYZ789")
        return

    key = args[0].upper()
    is_valid, message = is_key_valid(key)
    if is_valid:
        USER_KEYS[user_id] = key
        await update.message.reply_text("Key hợp lệ! Dùng /analyze hoặc /analyze_multi để phân tích mô hình.")
    else:
        await update.message.reply_text(f"Key không hợp lệ: {message}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /help."""
    user_id = update.effective_user.id
    contact_msg = "\nLiên hệ @Nhanoke để mua key và sử dụng."
    if user_id == ADMIN_ID:
        help_text = (
            "Hướng dẫn sử dụng (Admin):\n"
            "/start - Bắt đầu sử dụng bot\n"
            "/set_key <key> - Nhập key (không cần cho admin)\n"
            "/analyze - Phân tích mô hình cầu\n"
            "/analyze_multi <số_lượng_bản_ghi> <độ_dài:số_mô_hình> - Phân tích đa độ dài (VD: /analyze_multi 1000 5:10,6:15)\n"
            "/admin - Vào chế độ quản lý\n"
            "/create_key <thời gian> - Tạo key (ví dụ: /create_key 7d)\n"
            "/list_keys - Liệt kê tất cả key\n"
            "/delete_key <key> - Xóa key\n"
            "/help - Xem hướng dẫn này" + contact_msg
        )
    else:
        help_text = (
            "Hướng dẫn sử dụng:\n"
            "/start - Bắt đầu sử dụng bot\n"
            "/set_key <key> - Nhập key để truy cập\n"
            "/analyze - Phân tích mô hình cầu (yêu cầu key hợp lệ)\n"
            "/analyze_multi <số_lượng_bản_ghi> <độ_dài:số_mô_hình> - Phân tích đa độ dài (VD: /analyze_multi 1000 5:10,6:15)\n"
            "/help - Xem hướng dẫn này" + contact_msg
        )
    await update.message.reply_text(help_text)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /admin."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Bạn không có quyền admin!")
        return
    await update.message.reply_text(
        "Chào admin! Chọn:\n/create_key <thời gian> - Tạo key mới\n/list_keys - Liệt kê key\n/delete_key <key> - Xóa key\n/analyze - Phân tích\n/analyze_multi - Phân tích đa độ dài\n/help - Hướng dẫn"
    )

async def create_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /create_key."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Bạn không có quyền admin!")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Vui lòng nhập thời gian. Ví dụ: /create_key 7d (7 ngày)")
        return

    duration = args[0]
    key, result = create_key(duration)
    if key:
        await update.message.reply_text(f"Key mới: {key}\nHết hạn: {result}")
    else:
        await update.message.reply_text(f"Lỗi tạo key: {result}")

async def list_keys_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /list_keys."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Bạn không có quyền admin!")
        return
    key_list = list_keys()
    await update.message.reply_text(key_list)

async def delete_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /delete_key."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Bạn không có quyền admin!")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Vui lòng nhập key. Ví dụ: /delete_key ABC123XYZ789")
        return

    key = args[0].upper()
    success, message = delete_key(key)
    await update.message.reply_text(message)

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bắt đầu phân tích mô hình."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        if user_id not in USER_KEYS:
            await update.message.reply_text("Vui lòng nhập key bằng /set_key <key> trước.")
            return
        is_valid, message = is_key_valid(USER_KEYS[user_id])
        if not is_valid:
            await update.message.reply_text(f"Key không hợp lệ: {message}. Dùng /set_key để nhập key mới.")
            return

    if not os.path.exists("results_history_full.csv"):
        await update.message.reply_text("Dữ liệu chưa sẵn sàng. Vui lòng chờ main.py cập nhật lần đầu.")
        return

    await update.message.reply_text("Nhập số lượng bản ghi để phân tích (số nguyên, ví dụ: 1000, tối đa 2000):")
    return MAX_RESULTS

async def max_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý số lượng bản ghi và tiếp tục phân tích."""
    try:
        max_results = int(update.message.text)
        if max_results <= 0 or max_results > 2000:
            raise ValueError("Số lượng phải từ 1 đến 2000.")
        context.user_data["max_results"] = max_results

        await update.message.reply_text("Nhập độ dài chuỗi (số nguyên, ví dụ: 6):")
        return PATTERN_LENGTH
    except ValueError as e:
        await update.message.reply_text(f"Vui lòng nhập số nguyên từ 1 đến 2000. Lỗi: {str(e)}. Thử lại:")
        return MAX_RESULTS

async def pattern_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý độ dài chuỗi."""
    try:
        pattern_length = int(update.message.text)
        if pattern_length <= 0:
            raise ValueError
        context.user_data["pattern_length"] = pattern_length
        await update.message.reply_text("Nhập số mô hình muốn lấy (số nguyên, ví dụ: 5):")
        return TOP_K
    except ValueError:
        await update.message.reply_text("Vui lòng nhập số nguyên dương. Thử lại:")
        return PATTERN_LENGTH

async def top_k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý số mô hình và trả kết quả phân tích."""
    try:
        top_k = int(update.message.text)
        if top_k <= 0:
            raise ValueError
        context.user_data["top_k"] = top_k
        pattern_length = context.user_data["pattern_length"]
        max_results = context.user_data["max_results"]

        # Phân tích dữ liệu từ results_history_full.csv
        colors = read_results("results_history_full.csv", max_results)
        if colors is None or not colors:
            await update.message.reply_text("Lỗi đọc dữ liệu. Vui lòng kiểm tra results_history_full.csv.")
            return ConversationHandler.END

        patterns = generate_patterns(colors, pattern_length)
        if not patterns:
            await update.message.reply_text("Không đủ dữ liệu để phân tích.")
            return ConversationHandler.END

        top_patterns = analyze_patterns(patterns, top_k)
        if not top_patterns:
            await update.message.reply_text("Không tìm thấy mô hình nào.")
            return ConversationHandler.END

        # Tạo kết quả text
        result_text = f"Top {top_k} mô hình (độ dài {pattern_length}, từ {len(colors)} kết quả):\n"
        for i, (pattern, count) in enumerate(top_patterns, 1):
            result_text += f"{i}. {pattern}: {count} lần\n"

        # Lưu file
        output_file = f"patterns_{update.effective_user.id}.csv"
        saved_file = save_patterns(top_patterns, output_file)

        # Gửi kết quả
        await update.message.reply_text(result_text)
        if saved_file:
            with open(saved_file, "rb") as f:
                await update.message.reply_document(document=f, filename="patterns.csv")
            os.remove(saved_file)

        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Vui lòng nhập số nguyên dương. Thử lại:")
        return TOP_K

async def analyze_multi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /analyze_multi để phân tích nhiều độ dài và mô hình cùng lúc."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        if user_id not in USER_KEYS:
            await update.message.reply_text("Vui lòng nhập key bằng /set_key <key> trước.")
            return
        is_valid, message = is_key_valid(USER_KEYS[user_id])
        if not is_valid:
            await update.message.reply_text(f"Key không hợp lệ: {message}. Dùng /set_key để nhập key mới.")
            return

    if not os.path.exists("results_history_full.csv"):
        await update.message.reply_text("Dữ liệu chưa sẵn sàng. Vui lòng chờ main.py cập nhật.")
        return

    # Phân tích tham số từ lệnh
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Cú pháp không hợp lệ. Ví dụ: /analyze_multi 1000 5:10,6:15,7:20")
        return

    try:
        max_results = int(args[0])
        if max_results <= 0 or max_results > 2000:
            raise ValueError("Số lượng bản ghi phải từ 1 đến 2000.")
    except ValueError:
        await update.message.reply_text("Số lượng bản ghi không hợp lệ. Vui lòng nhập số nguyên từ 1 đến 2000.")
        return

    # Phân tích các cặp độ dài:số mô hình
    pairs = args[1].split(',')
    lengths = []
    models = []
    total_models = 0
    for pair in pairs:
        try:
            length, model = pair.split(':')
            length = int(length)
            model = int(model)
            if length <= 0 or model <= 0:
                raise ValueError
            lengths.append(length)
            models.append(model)
            total_models += model
        except ValueError:
            await update.message.reply_text(f"Cặp '{pair}' không hợp lệ. Vui lòng nhập theo định dạng độ_dài:số_mô_hình.")
            return

    if total_models > 250:
        await update.message.reply_text(f"Tổng số mô hình ({total_models}) vượt quá 250. Vui lòng điều chỉnh.")
        return

    # Đọc dữ liệu
    colors = read_results("results_history_full.csv", max_results)
    if colors is None or not colors:
        await update.message.reply_text("Lỗi đọc dữ liệu. Vui lòng kiểm tra results_history_full.csv.")
        return

    all_patterns = {}
    for length, model in zip(lengths, models):
        patterns = generate_patterns(colors, length)
        if not patterns:
            await update.message.reply_text(f"Không đủ dữ liệu cho độ dài {length}.")
            continue
        top_patterns = analyze_patterns(patterns, model)
        all_patterns[length] = top_patterns

    if not all_patterns:
        await update.message.reply_text("Không tìm thấy mô hình nào.")
        return

    # Lưu file CSV chỉ chứa các mô hình
    output_file = f"patterns_multi_{update.effective_user.id}.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        for length, patterns in all_patterns.items():
            for pattern, _ in patterns:
                writer.writerow([pattern])  # Chỉ ghi pattern, không có cột phụ

    # Gửi file CSV mà không xuất văn bản
    with open(output_file, "rb") as f:
        await update.message.reply_document(document=f, filename="patterns_multi.csv")
    os.remove(output_file)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hủy hội thoại."""
    await update.message.reply_text("Đã hủy phân tích.")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lỗi bot."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("Đã có lỗi xảy ra. Vui lòng thử lại sau.")

def main():
    """Chạy bot."""
    if not BOT_TOKEN or not ADMIN_ID:
        print("Error: BOT_TOKEN or ADMIN_ID not set in .env")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Hội thoại phân tích
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("analyze", analyze)],
        states={
            MAX_RESULTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_results)],
            PATTERN_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, pattern_length)],
            TOP_K: [MessageHandler(filters.TEXT & ~filters.COMMAND, top_k)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Thêm handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_key", set_key))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("create_key", create_key_command))
    application.add_handler(CommandHandler("list_keys", list_keys_command))
    application.add_handler(CommandHandler("delete_key", delete_key_command))
    application.add_handler(CommandHandler("analyze_multi", analyze_multi))
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    # Chạy bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
