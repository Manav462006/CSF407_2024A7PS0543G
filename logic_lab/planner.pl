% planner.pl  --  Optional extension: Prolog as a logical verifier
% Run with SWI-Prolog:   swipl planner.pl
% Then type queries, e.g.  ?- can_move(a,b).

% ---------------------------------------------------------------
% Task 6: warehouse knowledge (facts)
% ---------------------------------------------------------------
connected(a,b).
connected(b,a).
connected(b,c).
connected(c,b).

% Rule:  Connected(X,Y) -> CanMove(X,Y)
can_move(X,Y) :-
    connected(X,Y).

% ---------------------------------------------------------------
% Task 7: checking a proposed plan
% ---------------------------------------------------------------
valid_move(X,Y) :-
    connected(X,Y).

% Extra: check a whole sequence of moves, e.g.
%   ?- valid_path([move(a,b), move(b,c)]).
% Each move must be valid AND must start where the previous one ended.
valid_path([]).
valid_path([move(X,Y)]) :-
    valid_move(X,Y).
valid_path([move(X,Y), move(Y,Z) | Rest]) :-
    valid_move(X,Y),
    valid_path([move(Y,Z) | Rest]).

% ---------------------------------------------------------------
% Task 8: facts + rules -> inference
% ---------------------------------------------------------------
wet_road.

slippery :-
    wet_road.

reduce_speed :-
    slippery.
