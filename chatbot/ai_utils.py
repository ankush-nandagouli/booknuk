from datetime import date
from django.conf import settings
from books.models import IssuedBook, Book
from accounts.models import CustomUser
from django.utils.timezone import now
# ---------- Simple rule-based intent detection ----------
def detect_intent(text: str):
    """Return an intent tag and optional params."""
    t = text.lower().strip()

    if any(k in t for k in ("my books", "issued", "books i have", "my issued")):
        return "check_issued_books", {}

    if "fine" in t or "fines" in t or "due" in t:
        return "check_fines", {}

    if any(k in t for k in ("search book", "find", "do you have", "available")):
        title = ""
        if "search book" in t:
            title = t.replace("search book", "").strip(" ?")
        elif "find" in t:
            title = t.replace("find", "").strip(" ?")
        elif "do you have" in t:
            title = t.split("do you have", 1)[-1].strip(" ?")
        elif "available" in t:
            title = t.replace("available", "").strip(" ?")

        return "search_book", {"title": title}

    if any(k in t for k in ("hello", "hi", "hey")):
        return "greeting", {}

    return "unknown", {}

# ---------- Helpers: build reply for each intent ----------
def reply_check_issued_books(user):
    if not user or not getattr(user, "is_student", None) or not user.is_student():
        return "I can show issued books only for students. Please login as a student and try again."

    issued = IssuedBook.objects.filter(student=user, return_date__isnull=True).select_related("book")
    if not issued.exists():
        return "You currently have no books issued. ✅"

    lines = []
    today = date.today()
    for i in issued:
        fine = 0
        if i.due_date and today > i.due_date:
            fine = (today - i.due_date).days * getattr(settings, "LIB_FINE_RATE", 10)
        lines.append(f"- {i.book.title} | Issued: {i.issue_date} | Due: {i.due_date} | Fine: ₹{fine}")
    return "Here are your issued books:\n" + "\n".join(lines)

def reply_check_fines(user):
    if not user or not getattr(user, "is_student", None) or not user.is_student():
        return "I can check fines for students. Please login as a student."

    issued = IssuedBook.objects.filter(student=user, return_date__isnull=True)
    total = 0
    today = now()
    for i in issued:
        if i.due_date and today > i.due_date:
            total += (today - i.due_date).days * getattr(settings, "LIB_FINE_RATE", 10)

    if total == 0:
        return "You have no fines. ✅"
    return f"Your total fine is ₹{total}."

def reply_search_book(title: str):
    if not title:
        return "Please tell me the title or part of the title to search for."

    qs = Book.objects.filter(title__icontains=title) | Book.objects.filter(author__icontains=title)
    qs = qs.distinct()[:10]

    if not qs.exists():
        return f"No books found for '{title}'."

    lines = []
    for b in qs:
        lines.append(f"- {b.title} by {b.author or 'Unknown'} | Available: {'Yes' if getattr(b,'available',True) else 'No'}")
    return "Search results:\n" + "\n".join(lines)

# ---------- main router ----------
def handle_user_message(text, user=None):
    intent, params = detect_intent(text)

    if intent == "check_issued_books":
        return reply_check_issued_books(user)

    if intent == "check_fines":
        return reply_check_fines(user)

    if intent == "search_book":
        return reply_search_book(params.get("title"))

    if intent == "greeting":
        return "Hello! 👋 I can help with checking your issued books, fines, searching books, and more. Just ask me."

    if intent == "developer" or "developed" or "who coded you":
        return "Ankush Nandgouli is the developer of this Library Management System."
    return "Sorry, I didn’t understand that. Try asking about your books, fines, or searching for a title."
