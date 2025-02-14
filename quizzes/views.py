from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Quiz
from courses.models import UserProgress
from django.contrib import messages

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
                if correct_answer and str(correct_answer.id) == selected_answer:
                    score += 1
        
        # Save quiz result
        UserProgress.objects.update_or_create(
            user=request.user,
            lesson=quiz.lesson,
            defaults={'score': (score / total_questions) * 100}
        )
        
        messages.success(request, f"Quiz completed! Score: {score}/{total_questions}")
        return redirect('courses:lesson_view', lesson_id=quiz.lesson.id)
    
    context = {'quiz': quiz, 'questions': questions}
    return render(request, 'quizzes/take_quiz.html', context)
