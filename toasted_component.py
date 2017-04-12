from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession
from collections import defaultdict
import time
import json

QUESTION_TIMEOUT = 40.0
QUESTION_TIMEOUT_DIVISOR = 10.0
SCORES_FILENAME = '/home/jim/scores.txt'

class ToastedComponent(ApplicationSession):

    scores = defaultdict(float)
    current_question = None
    current_answers = None
    current_correct_answer = None
    current_points_multiplier = None
    current_responses = None    
    current_question_start_time = None

    @inlineCallbacks
    def onJoin(self, details):
        print("session joined")
        self._load_scores()
    
        yield self.register(self.get_current_scores, u"f_get_current_scores")
        yield self.register(self.answer_question, u"f_answer_question")
        
        yield self.register(self.set_question, u"f_set_question")
        yield self.register(self.tally_answers, u"f_tally_answers")
        yield self.register(self.get_team_answer, u"f_get_team_answer")
        yield self.register(self.get_insensitive_team_name, u"f_get_insensitive_team_name")
    
    def get_current_scores(self):
        return self.scores
    
    def get_insensitive_team_name(self, team_name):
        for iter_team_name in self.scores.iterkeys():
            if team_name.lower() == iter_team_name.lower():
                return iter_team_name
            
        return None
    
    def answer_question(self, team, answer):
        if team in self.current_responses:
            return
        
        self.current_responses[team] = answer
        self.current_response_times[team] = time.time() - self.current_question_start_time
        
        print "Answer " + answer + " received from team " + team + ", possible_points: " + str((QUESTION_TIMEOUT - self.current_response_times[team]) * self.current_points_multiplier);
        
        return QUESTION_TIMEOUT - self.current_response_times[team] #possible points earned here TODO: refactor so all of this handles points
        
    def set_question(self, question, points_multiplier, answers, correct_answer):
        self.current_correct_answer = correct_answer
        self.current_answers = answers
        self.current_question = question
        self.current_points_multiplier = float(points_multiplier)
        self.current_responses = defaultdict()
        self.current_response_times = defaultdict()
        self.current_question_start_time = time.time()
        
        self.publish(u'c_questions', question, points_multiplier, answers, self.current_question_start_time)
        print "Question received!"
                
    def get_team_answer(self, team):
        try:
            if team not in self.current_responses:
                return (None, self.current_correct_answer, 0.0)
            
            return (self.current_responses[team], self.current_correct_answer, self.current_points_multiplier * (QUESTION_TIMEOUT - self.current_response_times[team]))
        except Exception, ex:
            print str(ex)
            return None
    
    def tally_answers(self):
        for (team, answer) in self.current_responses.iteritems():
            if answer == self.current_correct_answer:
                points_for_question = (QUESTION_TIMEOUT - self.current_response_times[team])
                if points_for_question < 0:
                    print "Time_for_question is less than zero for team " + team
                    points_for_question = 0
                self.scores[team] += (self.current_points_multiplier * points_for_question)
            else:
                self.scores[team] -= self.current_points_multiplier * (QUESTION_TIMEOUT / QUESTION_TIMEOUT_DIVISOR)
        
        self._write_scores()
        self.publish(u'c_scores', self.scores, self.current_correct_answer)
        
        self.current_answers = None
        self.current_question = None
        self.current_points_multiplier = None
        self.current_responses = None
        self.current_correct_answer = None
        self.current_question_start_time = None
        
    def _write_scores(self):
        # save to file:
        with open(SCORES_FILENAME, 'w') as f:
            json.dump(self.scores, f)
    
    def _load_scores(self):
        # load from file:
        try:
            with open(SCORES_FILENAME, 'r') as f:
                self.scores = defaultdict(float, json.load(f))
            # if the file is empty the ValueError will be thrown
        except:
            self.scores = defaultdict(int)
        