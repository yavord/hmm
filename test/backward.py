def backward(X,A,E):
    """Given a single sequence, with Transition and Emission probabilities,
    return the Backward probability and corresponding trellis."""

    allStates = A.keys()
    emittingStates = E.keys()
    L = len(X) + 2

    # Initialize
    B = {k:[0] * L for k in allStates} # The Backward trellis
    for k in allStates:
        B[k][-2] = A[k]['E']

    #####################
    # START CODING HERE #
    #####################
    # Remaining columns
    # for i in range(L-3,-1,-1):
    #     s = seq[i]
    #     ...
    for i in range(L-3, -1, -1):
        s = X[i]
        for k in allStates:
            terms = [A[k][l]*E[l][s]*B[l][i+1] for l in emittingStates]
            B[k][i] =  sum(terms)

    #####################
    #  END CODING HERE  #
    #####################

    P = B['B'][0] # The Backward probability -- should be identical to Forward!
    return(P,B)