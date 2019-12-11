def forward(X,A,E):
    """Given a single sequence, with Transition and Emission probabilities,
    return the Forward probability and corresponding trellis."""

    allStates = A.keys()
    emittingStates = E.keys()
    L = len(X) + 2

    # Initialize
    F = {k:[0] * L for k in allStates}
    F['B'][0] = 1

    #####################
    # START CODING HERE #
    #####################
    # HINT: The Viterbi and Forward algorithm are very similar! 
    # Adapt the viterbi() function to account for the differences.

    # Middle columns
    # for ...
    for i,s in enumerate(X):
        for l in emittingStates:
            terms = [F[k][i] * A[k][l] for k in allStates]
            F[l][i+1] = sum(terms) * E[l][s]

    # Last columns
    # for ...:
    #     F['E'][-1] += ...
    for k in allStates:
        F['E'][-1] += F[k][i+1] * A[k]['E'] 

    #####################
    #  END CODING HERE  #
    #####################

    P = F['E'][-1] # The Forward probability: P(X|A,E)
    return(P,F)