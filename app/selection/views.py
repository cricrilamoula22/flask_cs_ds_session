#\my_app\app\selection\views.py :

from flask import render_template
from app.selection.forms import FilterForm
from app.selection.services import get_selected_items, get_subtotals

def render_selection_page(form, items, session_id):
    selected_items = get_selected_items(session_id)
    subtotals = get_subtotals(session_id)
    return render_template(
        'selection.html',
        form=form,
        items=items,
        selected_items=selected_items,
        subtotals=subtotals
    )
