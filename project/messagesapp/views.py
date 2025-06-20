from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import login as auth_login
from django.http import Http404
from django.forms import TextInput, PasswordInput
from .models import Message
from datetime import datetime
import sqlite3
import bleach

@login_required
def index(request):
    sent_messages_list = Message.objects.filter(sender=request.user.username).order_by('timestamp')
    received_messages_list = Message.objects.filter(recipient=request.user.username).order_by('timestamp')
    context = {
        'sent_messages_list': sent_messages_list,
        'received_messages_list': received_messages_list,
    }
    return render(request, 'messagesapp/index.html', context)

# Vulnerability: broken access control
# Users can view messages they are not authorized to see
# Fix:
# Remove comment from the @login_required decorator below to enforce login
#@login_required
def detail(request, message_id):
    message = get_object_or_404(Message, pk=message_id)
    # Fix: 
    # Check if the logged in user has permission to view the message
    # if message.sender != request.user.username and message.recipient != request.user.username:
    #    raise Http404("You do not have permission to view this message.")
    context = {'message': message}
    return render(request, 'messagesapp/detail.html', context)


# Vulnerability: CSRF
# Users can send messages without CSRF protection
# Fix:
# Remove the @csrf_exempt decorator below to enable CSRF protection
@csrf_exempt
def new_message(request):
    if request.method == 'POST':
        try:
            sender = request.user.username
            recipient = request.POST.get('recipient')
            content = request.POST.get('content')
            # Vulnerability: XSS 
            # No sanitization of user input before storing in database
            # Fix: 
            #content = bleach.clean(content, tags=[], attributes={}, strip=True)
            
            timestamp = datetime.now()
            new_message = Message(sender=sender, recipient=recipient, content=content, timestamp=timestamp)
            if recipient == "" or content  == "":
                raise ValueError("Missing required fields")
            else:
                new_message.save()  
                return redirect('messagesapp:index')
        except ValueError as e:
            print("Error: Missing required fields.")
            return render(request, 'messagesapp/new_message.html', {
                'error_message': e,
            })
    return render(request, 'messagesapp/new_message.html')
        

def register(request):
    if request.method == 'POST':
        print("Registering new user")
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('messagesapp:login')
        error_message = "Invalid registration details"
        return render(request, 'messagesapp/register.html', {'form': form, 'error_message': error_message})

    form = UserCreationForm()
    return render(request, 'messagesapp/register.html', {'form': form})

@csrf_exempt
def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('messagesapp:index')
        error_message = "Invalid login details"
        return render(request, 'messagesapp/login.html', {'form': form, 'error_message': error_message})

    form = AuthenticationForm(request)
    # Vulnerability: Weak password policy
    # The password is exposed in the HTML form
    # Fix:
    # Use a password input field instead of a text input field
    #form.fields['password'].widget = PasswordInput()
    form.fields['password'].widget = TextInput()
    return render(request, 'messagesapp/login.html', {'form': form})


def logout(request):
    auth_logout(request)
    return redirect('messagesapp:login')

@login_required
def search_messages(request):
    query = request.GET.get('query', '')
    messages = []
    username = request.user.username
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    # Vulnerability: SQL Injection  
    # With input: %' OR 1=1; -- , it shows all messages
    sql = "SELECT * FROM messagesapp_message WHERE (sender='" + username + "' OR recipient='" + username + "') AND content LIKE '%" + query + "%'"
    response = cursor.execute(sql).fetchall()
    # Fix:
    # Replace the above SQL query with the parameterized query below to prevent SQL injection
    #sql = "SELECT * FROM messagesapp_message WHERE (sender=? OR recipient=?) AND content LIKE ?"
    #params = (username, username, '%' + query + '%')
    #response = cursor.execute(sql, params).fetchall()

    for r in response:
        message = {
            'id': r[0],
            'sender': r[1],
            'recipient': r[2],
            'content': r[3],
            'timestamp': r[4],
        }
        messages.append(message)

    conn.close()
    context = {
        'messages': messages,
        'query': query,
    }
    return render(request, 'messagesapp/search_results.html', context)
