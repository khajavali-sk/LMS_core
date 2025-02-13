from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from .models import Quiz
from courses.models import UserProgress
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Create your views here.



@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.question_set.prefetch_related('answer_set').all()
    
    if request.method == 'POST':
        score = 0
        total_questions = questions.count()
        
        for question in questions:
            selected_answer = request.POST.get(f'question_{question.id}')
            if selected_answer:
                correct_answer = question.answer_set.filter(is_correct=True).first()
                if str(correct_answer.id) == selected_answer:
                    score += 1
        
        # Save quiz result
        UserProgress.objects.update_or_create(
            user=request.user,
            lesson=quiz.lesson,
            defaults={'score': (score/total_questions)*100}
        )
        
        messages.success(request, f"Quiz completed! Score: {score}/{total_questions}")
        return redirect('lesson_view', lesson_id=quiz.lesson.id)
    
    context = {'quiz': quiz, 'questions': questions}
    return render(request, 'quizzes/take_quiz.html', context)



def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if not request.user.is_authenticated or not quiz.lesson.module.course.enrollment_set.filter(user=request.user).exists():
        return HttpResponseForbidden()

    questions = quiz.question_set.prefetch_related('answer_set').order_by('order')
    results = None
    
    if request.method == 'POST':
        score = 0
        total = questions.count()
        results = []
        
        for question in questions:
            selected = request.POST.get(f'q_{question.id}')
            correct = question.answer_set.filter(is_correct=True).first()
            
            results.append({
                'question': question,
                'selected': selected,
                'correct': correct,
                'is_correct': str(correct.id) == selected if correct else False
            })
            
            if results[-1]['is_correct']:
                score += 1
                
        # Save quiz attempt
        QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=(score/total)*100
        )
        
        messages.success(request, f"You scored {score}/{total} ({round((score/total)*100)}%)")

    context = {
        'quiz': quiz,
        'questions': questions,
        'results': results
    }
    return render(request, 'quizzes/quiz_detail.html', context)