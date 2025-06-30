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

# Lưu key tạm thời cho người dùng và ngôn ngữ
USER_KEYS = {}
USER_LANGUAGES = {}  # Lưu ngôn ngữ của từng user (vi hoặc en)

# Từ điển ngôn ngữ
LANGUAGES = {
    "vi": {
        "start_admin": "Chào admin! Dùng /admin để quản lý, /analyze để phân tích, hoặc /help để xem hướng dẫn.",
        "start_user": "Chào mừng bạn! Vui lòng nhập key bằng /set_key <key> để sử dụng bot. Xem /help để biết thêm.",
        "contact_msg": "\nLiên hệ @Nhanoke để mua key và sử dụng.",
        "set_key_admin": "Admin không cần key. Dùng /analyze hoặc /admin.",
        "set_key_no_args": "Vui lòng nhập key. Ví dụ: /set_key ABC123XYZ789",
        "set_key_valid": "Key hợp lệ! Dùng /analyze hoặc /analyze_multi để phân tích mô hình.",
        "set_key_invalid": "Key không hợp lệ: {message}.",
        "help_admin": (
            "Hướng dẫn sử dụng (Admin):\n"
            "/start - Bắt đầu sử dụng bot\n"
            "/set_key <key> - Nhập key (không cần cho admin)\n"
            "/analyze - Phân tích mô hình cầu\n"
            "/analyze_multi <số_lượng_bản_ghi> <độ_dài:số_mô_hình> - Phân tích đa độ dài (VD: /analyze_multi 1000 5:10,6:15)\n"
            "/admin - Vào chế độ quản lý\n"
            "/create_key <thời gian> - Tạo key (ví dụ: /create_key 7d)\n"
            "/list_keys - Liệt kê tất cả key\n"
            "/delete_key <key> - Xóa key\n"
            "/help - Xem hướng dẫn này{contact_msg}"
        ),
        "help_user": (
            "Hướng dẫn sử dụng:\n"
            "/start - Bắt đầu sử dụng bot\n"
            "/set_key <key> - Nhập key để truy cập\n"
            "/analyze - Phân tích mô hình cầu (yêu cầu key hợp lệ)\n"
            "/analyze_multi <số_lượng_bản_ghi> <độ_dài:số_mô_hình> - Phân tích đa độ dài (VD: /analyze_multi 1000 5:10,6:15)\n"
            "/help - Xem hướng dẫn này{contact_msg}"
        ),
        "admin_welcome": "Chào admin! Chọn:\n/create_key <thời gian> - Tạo key mới\n/list_keys - Liệt kê key\n/delete_key <key> - Xóa key\n/analyze - Phân tích\n/analyze_multi - Phân tích đa độ dài\n/help - Hướng dẫn",
        "no_admin_rights": "Bạn không có quyền admin!",
        "create_key_no_args": "Vui lòng nhập thời gian. Ví dụ: /create_key 7d (7 ngày)",
        "create_key_success": "Key mới: {key}\nHết hạn: {result}",
        "create_key_error": "Lỗi tạo key: {result}",
        "list_keys_no_rights": "Bạn không có quyền admin!",
        "delete_key_no_args": "Vui lòng nhập key. Ví dụ: /delete_key ABC123XYZ789",
        "delete_key_result": "{message}",
        "analyze_no_key": "Vui lòng nhập key bằng /set_key <key> trước.",
        "analyze_invalid_key": "Key không hợp lệ: {message}. Dùng /set_key để nhập key mới.",
        "analyze_no_data": "Dữ liệu chưa sẵn sàng. Vui lòng chờ main.py cập nhật lần đầu.",
        "analyze_max_results": "Nhập số lượng bản ghi để phân tích (số nguyên, ví dụ: 1000, tối đa 2000):",
        "analyze_max_results_error": "Vui lòng nhập số nguyên từ 1 đến 2000. Lỗi: {e}. Thử lại:",
        "analyze_pattern_length": "Nhập độ dài chuỗi (số nguyên, ví dụ: 6):",
        "analyze_pattern_length_error": "Vui lòng nhập số nguyên dương. Thử lại:",
        "analyze_top_k": "Nhập số mô hình muốn lấy (số nguyên, ví dụ: 5):",
        "analyze_top_k_error": "Vui lòng nhập số nguyên dương. Thử lại:",
        "analyze_read_error": "Lỗi đọc dữ liệu. Vui lòng kiểm tra results_history_full.csv.",
        "analyze_no_patterns": "Không đủ dữ liệu để phân tích.",
        "analyze_no_top_patterns": "Không tìm thấy mô hình nào.",
        "analyze_result_text": "Top {top_k} mô hình (độ dài {pattern_length}, từ {len_colors} kết quả):\n",
        "analyze_pattern_format": "{i}. {pattern}: {count} lần\n",
        "analyze_multi_no_key": "Vui lòng nhập key bằng /set_key <key> trước.",
        "analyze_multi_invalid_key": "Key không hợp lệ: {message}. Dùng /set_key để nhập key mới.",
        "analyze_multi_no_data": "Dữ liệu chưa sẵn sàng. Vui lòng chờ main.py cập nhật.",
        "analyze_multi_invalid_syntax": "Cú pháp không hợp lệ. Ví dụ: /analyze_multi 1000 5:10,6:15,7:20",
        "analyze_multi_max_results_error": "Số lượng bản ghi không hợp lệ. Vui lòng nhập số nguyên từ 1 đến 2000.",
        "analyze_multi_pair_error": "Cặp '{pair}' không hợp lệ. Vui lòng nhập theo định dạng độ_dài:số_mô_hình.",
        "analyze_multi_total_exceeded": "Tổng số mô hình ({total_models}) vượt quá 250. Vui lòng điều chỉnh.",
        "analyze_multi_read_error": "Lỗi đọc dữ liệu. Vui lòng kiểm tra results_history_full.csv.",
        "analyze_multi_no_data_length": "Không đủ dữ liệu cho độ dài {length}.",
        "analyze_multi_no_patterns": "Không tìm thấy mô hình nào.",
        "cancel_message": "Đã hủy phân tích.",
        "error_message": "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
    },
    "en": {
        "start_admin": "Hello admin! Use /admin to manage, /analyze to analyze, or /help for instructions.",
        "start_user": "Welcome! Please enter a key with /set_key <key> to use the bot. See /help for more.",
        "contact_msg": "\nContact @Nhanoke to purchase a key and use.",
        "set_key_admin": "Admin does not need a key. Use /analyze or /admin.",
        "set_key_no_args": "Please enter a key. Example: /set_key ABC123XYZ789",
        "set_key_valid": "Valid key! Use /analyze or /analyze_multi to analyze patterns.",
        "set_key_invalid": "Invalid key: {message}.",
        "help_admin": (
            "User Guide (Admin):\n"
            "/start - Start using the bot\n"
            "/set_key <key> - Enter key (not required for admin)\n"
            "/analyze - Analyze patterns\n"
            "/analyze_multi <record_count> <length:model_count> - Multi-length analysis (e.g., /analyze_multi 1000 5:10,6:15)\n"
            "/admin - Enter management mode\n"
            "/create_key <duration> - Create key (e.g., /create_key 7d)\n"
            "/list_keys - List all keys\n"
            "/delete_key <key> - Delete key\n"
            "/help - View this guide{contact_msg}"
        ),
        "help_user": (
            "User Guide:\n"
            "/start - Start using the bot\n"
            "/set_key <key> - Enter key to access\n"
            "/analyze - Analyze patterns (requires valid key)\n"
            "/analyze_multi <record_count> <length:model_count> - Multi-length analysis (e.g., /analyze_multi 1000 5:10,6:15)\n"
            "/help - View this guide{contact_msg}"
        ),
        "admin_welcome": "Hello admin! Choose:\n/create_key <duration> - Create new key\n/list_keys - List keys\n/delete_key <key> - Delete key\n/analyze - Analyze\n/analyze_multi - Multi-length analysis\n/help - Help",
        "no_admin_rights": "You do not have admin rights!",
        "create_key_no_args": "Please enter duration. Example: /create_key 7d (7 days)",
        "create_key_success": "New key: {key}\nExpires: {result}",
        "create_key_error": "Key creation error: {result}",
        "list_keys_no_rights": "You do not have admin rights!",
        "delete_key_no_args": "Please enter a key. Example: /delete_key ABC123XYZ789",
        "delete_key_result": "{message}",
        "analyze_no_key": "Please enter a key with /set_key <key> first.",
        "analyze_invalid_key": "Invalid key: {message}. Use /set_key to enter a new key.",
        "analyze_no_data": "Data is not ready. Please wait for main.py to update.",
        "analyze_max_results": "Enter the number of records to analyze (integer, e.g., 1000, max 2000):",
        "analyze_max_results_error": "Please enter an integer from 1 to 2000. Error: {e}. Try again:",
        "analyze_pattern_length": "Enter sequence length (integer, e.g., 6):",
        "analyze_pattern_length_error": "Please enter a positive integer. Try again:",
        "analyze_top_k": "Enter the number of models to retrieve (integer, e.g., 5):",
        "analyze_top_k_error": "Please enter a positive integer. Try again:",
        "analyze_read_error": "Error reading data. Please check results_history_full.csv.",
        "analyze_no_patterns": "Not enough data to analyze.",
        "analyze_no_top_patterns": "No patterns found.",
        "analyze_result_text": "Top {top_k} models (length {pattern_length}, from {len_colors} results):\n",
        "analyze_pattern_format": "{i}. {pattern}: {count} times\n",
        "analyze_multi_no_key": "Please enter a key with /set_key <key> first.",
        "analyze_multi_invalid_key": "Invalid key: {message}. Use /set_key to enter a new key.",
        "analyze_multi_no_data": "Data is not ready. Please wait for main.py to update.",
        "analyze_multi_invalid_syntax": "Invalid syntax. Example: /analyze_multi 1000 5:10,6:15,7:20",
        "analyze_multi_max_results_error": "Invalid number of records. Please enter an integer from 1 to 2000.",
        "analyze_multi_pair_error": "Pair '{pair}' is invalid. Please use format length:model_count.",
        "analyze_multi_total_exceeded": "Total models ({total_models}) exceed 250. Please adjust.",
        "analyze_multi_read_error": "Error reading data. Please check results_history_full.csv.",
        "analyze_multi_no_data_length": "Not enough data for length {length}.",
        "analyze_multi_no_patterns": "No patterns found.",
        "cancel_message": "Analysis canceled.",
        "error_message": "An error occurred. Please try again later.",
    }
}

def get_lang_text(lang, key, **kwargs):
    """Lấy văn bản theo ngôn ngữ và thay thế tham số nếu có."""
    text = LANGUAGES.get(lang, LANGUAGES["vi"]).get(key, "")
    return text.format(**kwargs, contact_msg=LANGUAGES[lang]["contact_msg"]) if kwargs else text

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /vi hoặc /en để thay đổi ngôn ngữ."""
    user_id = update.effective_user.id
    lang = update.message.text[1:].lower()  # Lấy 'vi' hoặc 'en' từ lệnh
    if lang in LANGUAGES:
        USER_LANGUAGES[user_id] = lang
        await update.message.reply_text(get_lang_text(lang, "start_user" if user_id != ADMIN_ID else "start_admin"))
    else:
        await update.message.reply_text("Language not supported. Use /vi for Vietnamese or /en for English.")
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")  # Mặc định là tiếng Việt
    contact_msg = get_lang_text(lang, "contact_msg")
    if user_id == ADMIN_ID:
        await update.message.reply_text(get_lang_text(lang, "start_admin") + contact_msg)
    else:
        await update.message.reply_text(get_lang_text(lang, "start_user") + contact_msg)

async def set_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /set_key."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    if user_id == ADMIN_ID:
        await update.message.reply_text(get_lang_text(lang, "set_key_admin"))
        return

    args = context.args
    if not args:
        await update.message.reply_text(get_lang_text(lang, "set_key_no_args"))
        return

    key = args[0].upper()
    is_valid, message = is_key_valid(key)
    if is_valid:
        USER_KEYS[user_id] = key
        await update.message.reply_text(get_lang_text(lang, "set_key_valid"))
    else:
        await update.message.reply_text(get_lang_text(lang, "set_key_invalid").format(message=message))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /help."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    if user_id == ADMIN_ID:
        await update.message.reply_text(get_lang_text(lang, "help_admin"))
    else:
        await update.message.reply_text(get_lang_text(lang, "help_user"))

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /admin."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    if user_id != ADMIN_ID:
        await update.message.reply_text(get_lang_text(lang, "no_admin_rights"))
        return
    await update.message.reply_text(get_lang_text(lang, "admin_welcome"))

async def create_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /create_key."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    if user_id != ADMIN_ID:
        await update.message.reply_text(get_lang_text(lang, "no_admin_rights"))
        return

    args = context.args
    if not args:
        await update.message.reply_text(get_lang_text(lang, "create_key_no_args"))
        return

    duration = args[0]
    key, result = create_key(duration)
    if key:
        await update.message.reply_text(get_lang_text(lang, "create_key_success").format(key=key, result=result))
    else:
        await update.message.reply_text(get_lang_text(lang, "create_key_error").format(result=result))

async def list_keys_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /list_keys."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    if user_id != ADMIN_ID:
        await update.message.reply_text(get_lang_text(lang, "list_keys_no_rights"))
        return
    key_list = list_keys()
    await update.message.reply_text(key_list)

async def delete_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /delete_key."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    if user_id != ADMIN_ID:
        await update.message.reply_text(get_lang_text(lang, "list_keys_no_rights"))
        return

    args = context.args
    if not args:
        await update.message.reply_text(get_lang_text(lang, "delete_key_no_args"))
        return

    key = args[0].upper()
    success, message = delete_key(key)
    await update.message.reply_text(get_lang_text(lang, "delete_key_result").format(message=message))

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bắt đầu phân tích mô hình."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    if user_id != ADMIN_ID:
        if user_id not in USER_KEYS:
            await update.message.reply_text(get_lang_text(lang, "analyze_no_key"))
            return
        is_valid, message = is_key_valid(USER_KEYS[user_id])
        if not is_valid:
            await update.message.reply_text(get_lang_text(lang, "analyze_invalid_key").format(message=message))
            return

    if not os.path.exists("results_history_full.csv"):
        await update.message.reply_text(get_lang_text(lang, "analyze_no_data"))
        return

    await update.message.reply_text(get_lang_text(lang, "analyze_max_results"))
    return MAX_RESULTS

async def max_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý số lượng bản ghi và tiếp tục phân tích."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    try:
        max_results = int(update.message.text)
        if max_results <= 0 or max_results > 2000:
            raise ValueError("Số lượng phải từ 1 đến 2000.")
        context.user_data["max_results"] = max_results

        await update.message.reply_text(get_lang_text(lang, "analyze_pattern_length"))
        return PATTERN_LENGTH
    except ValueError as e:
        await update.message.reply_text(get_lang_text(lang, "analyze_max_results_error").format(e=str(e)))
        return MAX_RESULTS

async def pattern_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý độ dài chuỗi."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    try:
        pattern_length = int(update.message.text)
        if pattern_length <= 0:
            raise ValueError
        context.user_data["pattern_length"] = pattern_length
        await update.message.reply_text(get_lang_text(lang, "analyze_top_k"))
        return TOP_K
    except ValueError:
        await update.message.reply_text(get_lang_text(lang, "analyze_pattern_length_error"))
        return PATTERN_LENGTH

async def top_k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý số mô hình và trả kết quả phân tích."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
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
            await update.message.reply_text(get_lang_text(lang, "analyze_read_error"))
            return ConversationHandler.END

        patterns = generate_patterns(colors, pattern_length)
        if not patterns:
            await update.message.reply_text(get_lang_text(lang, "analyze_no_patterns"))
            return ConversationHandler.END

        top_patterns = analyze_patterns(patterns, top_k)
        if not top_patterns:
            await update.message.reply_text(get_lang_text(lang, "analyze_no_top_patterns"))
            return ConversationHandler.END

        # Tạo kết quả text
        result_text = get_lang_text(lang, "analyze_result_text").format(top_k=top_k, pattern_length=pattern_length, len_colors=len(colors))
        for i, (pattern, count) in enumerate(top_patterns, 1):
            result_text += get_lang_text(lang, "analyze_pattern_format").format(i=i, pattern=pattern, count=count)

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
        await update.message.reply_text(get_lang_text(lang, "analyze_top_k_error"))
        return TOP_K

async def analyze_multi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /analyze_multi để phân tích nhiều độ dài và mô hình cùng lúc."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    if user_id != ADMIN_ID:
        if user_id not in USER_KEYS:
            await update.message.reply_text(get_lang_text(lang, "analyze_multi_no_key"))
            return
        is_valid, message = is_key_valid(USER_KEYS[user_id])
        if not is_valid:
            await update.message.reply_text(get_lang_text(lang, "analyze_multi_invalid_key").format(message=message))
            return

    if not os.path.exists("results_history_full.csv"):
        await update.message.reply_text(get_lang_text(lang, "analyze_multi_no_data"))
        return

    # Phân tích tham số từ lệnh
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(get_lang_text(lang, "analyze_multi_invalid_syntax"))
        return

    try:
        max_results = int(args[0])
        if max_results <= 0 or max_results > 2000:
            raise ValueError("Số lượng bản ghi phải từ 1 đến 2000.")
    except ValueError:
        await update.message.reply_text(get_lang_text(lang, "analyze_multi_max_results_error"))
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
            await update.message.reply_text(get_lang_text(lang, "analyze_multi_pair_error").format(pair=pair))
            return

    if total_models > 250:
        await update.message.reply_text(get_lang_text(lang, "analyze_multi_total_exceeded").format(total_models=total_models))
        return

    # Đọc dữ liệu
    colors = read_results("results_history_full.csv", max_results)
    if colors is None or not colors:
        await update.message.reply_text(get_lang_text(lang, "analyze_multi_read_error"))
        return

    all_patterns = {}
    for length, model in zip(lengths, models):
        patterns = generate_patterns(colors, length)
        if not patterns:
            await update.message.reply_text(get_lang_text(lang, "analyze_multi_no_data_length").format(length=length))
            continue
        top_patterns = analyze_patterns(patterns, model)
        all_patterns[length] = top_patterns

    if not all_patterns:
        await update.message.reply_text(get_lang_text(lang, "analyze_multi_no_patterns"))
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
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    await update.message.reply_text(get_lang_text(lang, "cancel_message"))
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lỗi bot."""
    user_id = update.effective_user.id
    lang = USER_LANGUAGES.get(user_id, "vi")
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text(get_lang_text(lang, "error_message"))

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

    # Thêm handler cho ngôn ngữ
    application.add_handler(CommandHandler("vi", set_language))
    application.add_handler(CommandHandler("en", set_language))

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
