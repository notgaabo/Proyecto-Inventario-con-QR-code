from flask import render_template, session, redirect, url_for
from auth.auth import is_authenticated

def home_controller():
    if not is_authenticated():
        return redirect(url_for('login'))

    user = session['user']
    if user['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('statistics'))

def statistics_controller():
    if not is_authenticated():
        return redirect(url_for('login'))

    user = session['user']
    return render_template('user/statistics.html', user=user)
