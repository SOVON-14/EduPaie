from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "Schema_BDD_EduPaie.pdf"
PAGE_WIDTH, PAGE_HEIGHT = A4
INK = colors.HexColor("#173B36")
ACCENT = colors.HexColor("#287A5D")
PALE = colors.HexColor("#EDF4F0")
MUTED = colors.HexColor("#64736F")
BORDER = colors.HexColor("#D6E2DC")
TEXT = colors.HexColor("#293833")
WHITE = colors.white


def draw_page_header(pdf, title, subtitle, page_number):
    pdf.setFillColor(INK)
    pdf.rect(0, PAGE_HEIGHT - 31 * mm, PAGE_WIDTH, 31 * mm, fill=1, stroke=0)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 17)
    pdf.drawString(18 * mm, PAGE_HEIGHT - 16 * mm, title)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(18 * mm, PAGE_HEIGHT - 23 * mm, subtitle)

    pdf.setStrokeColor(BORDER)
    pdf.setLineWidth(0.6)
    pdf.line(18 * mm, 15 * mm, PAGE_WIDTH - 18 * mm, 15 * mm)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(18 * mm, 10.5 * mm, "EduPaie | SQLite | Schéma version 1")
    pdf.drawRightString(PAGE_WIDTH - 18 * mm, 10.5 * mm, f"Page {page_number} / 2")


def draw_entity(pdf, x, y, width, title, fields):
    header_height = 12 * mm
    row_height = 9 * mm
    height = header_height + row_height * len(fields)

    pdf.setFillColor(WHITE)
    pdf.setStrokeColor(BORDER)
    pdf.roundRect(x, y, width, height, 2 * mm, fill=1, stroke=1)
    pdf.setFillColor(ACCENT)
    pdf.roundRect(x, y + height - header_height, width, header_height, 2 * mm, fill=1, stroke=0)
    pdf.rect(x, y + height - header_height, width, 2 * mm, fill=1, stroke=0)

    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(x + 5 * mm, y + height - 7.8 * mm, title)

    top = y + height - header_height
    for index, (field, detail, key_type) in enumerate(fields):
        row_top = top - index * row_height
        row_bottom = row_top - row_height
        if index % 2 == 1:
            pdf.setFillColor(PALE)
            pdf.rect(x + 0.3 * mm, row_bottom, width - 0.6 * mm, row_height, fill=1, stroke=0)
        pdf.setStrokeColor(BORDER)
        pdf.setLineWidth(0.35)
        pdf.line(x, row_bottom, x + width, row_bottom)

        pdf.setFillColor(ACCENT if key_type else TEXT)
        pdf.setFont("Helvetica-Bold" if key_type else "Helvetica", 7.7)
        field_label = f"{key_type} {field}" if key_type else field
        pdf.drawString(x + 4 * mm, row_bottom + 3.2 * mm, field_label)

        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 6.8)
        pdf.drawRightString(x + width - 4 * mm, row_bottom + 3.2 * mm, detail)

    return height


def draw_relationship(pdf, left_x, right_x, center_y):
    pdf.setStrokeColor(ACCENT)
    pdf.setFillColor(ACCENT)
    pdf.setLineWidth(1.5)
    pdf.line(left_x, center_y, right_x - 2 * mm, center_y)
    pdf.line(right_x - 2 * mm, center_y, right_x - 5 * mm, center_y + 2 * mm)
    pdf.line(right_x - 2 * mm, center_y, right_x - 5 * mm, center_y - 2 * mm)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(left_x + 2 * mm, center_y + 4 * mm, "1")
    pdf.drawCentredString(right_x - 4 * mm, center_y + 4 * mm, "0..N")
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString((left_x + right_x) / 2, center_y + 4 * mm, "effectue")


def draw_mcd_page(pdf):
    draw_page_header(
        pdf,
        "Schéma de la base de données",
        "MCD / UML simplifié — EduPaie",
        1,
    )

    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(18 * mm, PAGE_HEIGHT - 42 * mm, "Modèle entité-association")
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(
        18 * mm,
        PAGE_HEIGHT - 48 * mm,
        "Clés : PK = clé primaire, FK = clé étrangère. Les montants sont stockés en FCFA entiers.",
    )

    left_x = 18 * mm
    right_x = PAGE_WIDTH - 18 * mm - 82 * mm
    box_width = 82 * mm
    box_y = 67 * mm

    student_fields = [
        ("id", "INTEGER AUTOINCREMENT", "PK"),
        ("nom", "TEXT NOT NULL", None),
        ("prenom", "TEXT NOT NULL", None),
        ("classe", "TEXT NOT NULL", None),
        ("annee_scolaire", "TEXT NOT NULL", None),
        ("montant_total", "INTEGER > 0", None),
        ("date_creation", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", None),
        ("(nom, prenom, classe, annee_scolaire)", "UNIQUE", "UQ"),
    ]
    payment_fields = [
        ("id", "INTEGER AUTOINCREMENT", "PK"),
        ("student_id", "INTEGER NOT NULL", "FK"),
        ("montant", "INTEGER > 0", None),
        ("date", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", None),
        ("mode_paiement", "4 valeurs autorisées", None),
        ("numero_recu", "TEXT NOT NULL UNIQUE", None),
    ]
    left_height = draw_entity(pdf, left_x, box_y, box_width, "STUDENTS — Élèves", student_fields)
    right_height = draw_entity(pdf, right_x, box_y, box_width, "PAYMENTS — Paiements", payment_fields)

    relation_y = box_y + min(left_height, right_height) / 2
    draw_relationship(pdf, left_x + box_width + 1 * mm, right_x - 1 * mm, relation_y)

    note_y = 51 * mm
    pdf.setFillColor(PALE)
    pdf.roundRect(18 * mm, note_y - 20 * mm, PAGE_WIDTH - 36 * mm, 20 * mm, 2 * mm, fill=1, stroke=0)
    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(23 * mm, note_y - 7 * mm, "Cardinalités")
    pdf.setFillColor(TEXT)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(23 * mm, note_y - 13 * mm, "Un élève possède 0 à N paiements; chaque paiement appartient à exactement 1 élève.")
    pdf.drawString(23 * mm, note_y - 18 * mm, "La clé étrangère payments.student_id référence students.id avec ON DELETE CASCADE.")

    index_y = 22 * mm
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawString(18 * mm, index_y, "INDEX")
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(38 * mm, index_y, "idx_payments_student_id(student_id)  ·  idx_students_classe(classe)")
    pdf.showPage()


def sql_lines():
    return [
        "-- Création du schéma EduPaie — SQLite, version 1",
        "-- Activer les clés étrangères pour chaque connexion applicative.",
        "PRAGMA foreign_keys = ON;",
        "",
        "CREATE TABLE IF NOT EXISTS students (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    nom TEXT NOT NULL,",
        "    prenom TEXT NOT NULL,",
        "    classe TEXT NOT NULL,",
        "    annee_scolaire TEXT NOT NULL,",
        "    montant_total INTEGER NOT NULL CHECK(montant_total > 0),",
        "    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,",
        "    UNIQUE(nom, prenom, classe, annee_scolaire)",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS payments (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    student_id INTEGER NOT NULL,",
        "    montant INTEGER NOT NULL CHECK(montant > 0),",
        "    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,",
        "    mode_paiement TEXT NOT NULL CHECK(mode_paiement IN (",
        "        'especes', 'cheque', 'virement', 'mobile_money'",
        "    )),",
        "    numero_recu TEXT NOT NULL UNIQUE,",
        "    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE",
        ");",
        "",
        "CREATE INDEX IF NOT EXISTS idx_payments_student_id",
        "    ON payments(student_id);",
        "",
        "CREATE INDEX IF NOT EXISTS idx_students_classe",
        "    ON students(classe);",
    ]


def draw_sql_page(pdf):
    draw_page_header(
        pdf,
        "Script SQL de création",
        "SQLite — tables, contraintes et index, conforme à database/schema.sql",
        2,
    )
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(18 * mm, PAGE_HEIGHT - 42 * mm, "À exécuter sur une base SQLite neuve. La migration des bases existantes est gérée par database.py.")

    code_x = 20 * mm
    code_top = PAGE_HEIGHT - 53 * mm
    font_name = "Courier"
    font_size = 7.4
    leading = 9.2
    code_lines = sql_lines()
    code_height = len(code_lines) * leading + 12
    code_width = PAGE_WIDTH - 40 * mm
    code_bottom = code_top - code_height

    pdf.setFillColor(colors.HexColor("#F5F8F6"))
    pdf.setStrokeColor(BORDER)
    pdf.roundRect(code_x - 3 * mm, code_bottom, code_width + 6 * mm, code_height, 2 * mm, fill=1, stroke=1)

    y = code_top - 10
    for line in code_lines:
        if line.startswith("--"):
            pdf.setFillColor(MUTED)
        elif line.startswith("CREATE") or line.startswith("PRAGMA"):
            pdf.setFillColor(ACCENT)
        else:
            pdf.setFillColor(TEXT)
        pdf.setFont(font_name, font_size)
        if stringWidth(line, font_name, font_size) > code_width:
            raise ValueError(f"Ligne SQL trop longue pour le PDF : {line}")
        pdf.drawString(code_x, y, line)
        y -= leading

    note_y = code_bottom - 10 * mm
    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(18 * mm, note_y, "Règles appliquées")
    notes = [
        "Montants entiers strictement positifs; devise de l’application : FCFA.",
        "Unicité d’un élève par nom, prénom, classe et année scolaire.",
        "Modes autorisés : espèces, chèque, virement ou Mobile Money (codes SQL indiqués ci-dessus).",
        "Suppression d’un élève : ses paiements sont supprimés en cascade.",
        "Les index accélèrent la recherche des paiements par élève et le filtrage des élèves par classe.",
    ]
    pdf.setFillColor(TEXT)
    pdf.setFont("Helvetica", 7.5)
    y = note_y - 6 * mm
    for note in notes:
        pdf.drawString(21 * mm, y, "• " + note)
        y -= 5 * mm

    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica-Oblique", 7)
    pdf.drawString(18 * mm, 20 * mm, "Source : database/schema.sql | Activation des clés étrangères par connexion : database/database.py")
    pdf.showPage()


def generate_pdf(path=OUTPUT_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    pdf.setTitle("EduPaie — Schéma de la base de données")
    pdf.setAuthor("EduPaie")
    pdf.setSubject("MCD et script SQL SQLite")
    draw_mcd_page(pdf)
    draw_sql_page(pdf)
    pdf.save()
    return path


if __name__ == "__main__":
    print(generate_pdf())
