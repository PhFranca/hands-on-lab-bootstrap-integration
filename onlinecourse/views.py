from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .models import Course, Lesson, Enrollment
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
from django.urls import reverse
from django.views import generic, View
from collections import defaultdict
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your views here.
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    enrollment = Enrollment.objects.filter(user=user, course=course).get()
   
    submission = Submission.objects.create(enrollment_id = enrollment.id )

    answers =  extract_answers(request)
    for a in answers:
        temp_c = Choice.objects.filter(id = int(a)).get()
        submission.choices.add(temp_c)

    submission.save()         
    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course.id,submission.id ))) 

# Create authentication related views


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.debug("{} is new user".format(username))
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:popular_course_list")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration.html', context)

def show_exam_result(request, course_id, submission_id):
    course  =  get_object_or_404(Course, pk=course_id)
    submission =      get_object_or_404(Submission, pk=submission_id)
    total =  0
    total_user =  0
    q_results = {}
    c_submits = {}
    c_results = {}
    for q in course.question_set.all():
        q_total = 0
        q_total_user = 0
        for c in q.choice_set.all():
            q_total += 1  
            temp_right = c.is_correct
            count =  submission.choices.filter(id = c.id).count()

            temp_user  = count > 0 
            c_submits[c.id] = temp_user
            c_results[c.id] = temp_user == temp_right
            if temp_user == temp_right:
                q_total_user += 1        
        q_results[q.id] =  q.grade*(q_total_user / q_total)
        total += q.grade 
        total_user  += q_results[q.id]
    context  = {}
    context["course"]  =  course
    context["submission"]  =  submission
    #context["choices"]  =  submission.chocies.all()
    context["total"]  =  total
    context["total_user"]  =  total_user
    context["q_results"]  =  q_results
    context["c_submits"]  =  c_submits
    context["c_results"]  =  c_results
    context["grade"]  =  int((total_user/total)*100)
    #print(vars(submission.chocies))
    #user = request.user
    #return render(request, 'onlinecourse/show_exam_result.html', context)
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)

##
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        print(user)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:popular_course_list')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login.html', context)
    else:
        return render(request, 'onlinecourse/user_login.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:popular_course_list')


# Add a class-based course list view
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list.html'
    context_object_name = 'course_list'

    def get_queryset(self):
       courses = Course.objects.order_by('-total_enrollment')[:10]
       return courses


# Add a generic course details view
class CourseDetailsView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail.html'


class EnrollView(View):

    # Handles get request
    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('pk')
        course = get_object_or_404(Course, pk=course_id)
        # Create an enrollment
        course.total_enrollment += 1
        course.save()
        return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))
