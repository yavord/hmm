#!/usr/bin/python3


import os.path as op

from os import makedirs
from math import log10
from hmm_utility import parse_args, load_fasta, load_tsv, print_trellis, print_params, serialize



def viterbi(X,A,E):
    """Given a single sequence, with Transition and Emission probabilities,
    return the most probable state path, the corresponding P(X), and trellis."""

    allStates = A.keys()
    emittingStates = E.keys()
    L = len(X) + 2

    # Initialize
    V = {k:[0] * L for k in allStates} # The Viterbi trellis
    V['B'][0] = 1.

    # Middle columns
    for i,s in enumerate(X):
        for l in emittingStates:
            terms = [V[k][i] * A[k][l] for k in allStates]
            V[l][i+1] = max(terms) * E[l][s]

    # Last column
    for k in allStates:
        term = V[k][i+1] * A[k]['E'] 
        if term > V['E'][-1]:
            V['E'][-1] = term
            pi = k # Last state of the State Path

    # FOR VITERBI ONLY: Trace back the State Path
    l = pi
    i = L-2
    while i:
        i -= 1
        for k in emittingStates:
            if V[k][i] * A[k][l] * E[l][X[i]] == V[l][i+1]:
                pi = k + pi
                l = k
                break

    P = V['E'][-1] # The Viterbi probability: P(X,pi|A,E)
    return(pi,P,V) # Return the state path, Viterbi probability, and Viterbi trellis



def forward(X,A,E):
    """Given a single sequence, with Transition and Emission probabilities,
    return the Forward probability and corresponding trellis."""

    allStates = A.keys()
    emittingStates = E.keys()
    L = len(X) + 2

    # Initialize
    F = {k:[0] * L for k in allStates}
    F['B'][0] = 1

    for i,s in enumerate(X):
        for l in emittingStates:
            terms = [F[k][i] * A[k][l] for k in allStates]
            F[l][i+1] = sum(terms) * E[l][s]

    for k in allStates:
        F['E'][-1] += F[k][i+1] * A[k]['E'] 

    P = F['E'][-1] # The Forward probability: P(X|A,E)
    return(P,F)



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

    for i in range(L-3, -1, -1):
        s = X[i]
        for k in allStates:
            terms = [A[k][l]*E[l][s]*B[l][i+1] for l in emittingStates]
            B[k][i] =  sum(terms)

    P = B['B'][0] # The Backward probability -- should be identical to Forward!
    return(P,B)



def baumwelch(set_X,A,E):
    """Given a set of sequences X and priors A and E,
    return the Sum Log Likelihood of X given the priors,
    along with the calculated posteriors for A and E."""

    allStates = A.keys()
    emittingStates = E.keys()
    emittingValues = E['L'].keys()

    # Initialize a new (posterior) Transition and Emission matrix
    new_A = {}
    for k in A:
        new_A[k] = {l:0 for l in A[k]}
    
    new_E = {}
    for k in E:
        new_E[k] = {s:0 for s in E[k]}

    # Iterate through all sequences in X
    SLL = 0 # Sum Log-Likelihood
    for X in set_X:
        P,F = forward(X,A,E)  # Save both the forward probability and the forward trellis
        _,B = backward(X,A,E) # Forward P == Backward P, so only save the backward trellis
        SLL += log10(P)
        
        for k in allStates:
            for l in emittingStates:
                for i in range(len(X)-1):
                    contributionA = (F[k][i] * A[k][l] * E[l][X[i+1]] * B[l][i+1])/P
                    new_A[k][l] += contributionA
        
        for k in emittingStates:
            for s in emittingValues:
                for i in range(len(X)-1):
                    if s == X[i]:
                        contributionE = (F[k][i] * B[k][i])/P
                        new_E[k][s] += contributionE

        for k in allStates:
            new_A[k]['E'] += (F[k][len(X)]*A[k]['E'])/P

    n_A = {}
    for k in A:
        n_A[k] = {l:0 for l in A[k]}

    n_E = {}
    for k in E:
        n_E[k] = {s:0 for s in E[k]}

    for k in allStates:
        total = 0
        for l in allStates:
            total += new_A[k][l]
        for l in allStates:
            if total == 0:
                n_A[k][l] = 0
            else:
                n_A[k][l] = new_A[k][l]/total

    for k in emittingStates:
        total = 0
        for l in emittingValues:
            total += new_E[k][l]
        for l in emittingValues:
            if total == 0:
                n_E[k][l] = 0
            else:
                n_E[k][l] = new_E[k][l]/total

    new_A = n_A
    new_E = n_E

    #####################
    #  END CODING HERE  #
    #####################

    return(SLL,new_A,new_E)



def main(args = False):
    "Perform the specified algorithm, for a given set of sequences and parameters."
    
    # Process arguments and load specified files
    if not args: args = parse_args()

    cmd = args.command            # viterbi, forward, backward or baumwelch
    verbosity = args.verbosity
    set_X, labels = load_fasta(args.fasta)  # List of sequences, list of labels
    A = load_tsv(args.transition) # Nested Q -> Q dictionary
    E = load_tsv(args.emission)   # Nested Q -> S dictionary
    
    def save(filename, contents):
        if args.out_dir:
            makedirs(args.out_dir, exist_ok=True) # Make sure the output directory exists.
            path = op.join(args.out_dir,filename)
            with open(path,'w') as f: f.write(contents)
        # Note this function does nothing if no out_dir is specified!



    # VITERBI
    if cmd == 'viterbi':
        for j,X in enumerate(set_X): # For every sequence:
            # Calculate the most probable state path, with the corresponding probability and matrix
            Q, P, T = viterbi(X,A,E)

            # Save and/or print relevant output
            label = labels[j]
            save('%s.path' % label, Q)
            save('%s.matrix' % label, serialize(T,X))
            save('%s.p' % label, '%1.2e' % P)
            print('>%s\n Path = %s' % (label,Q))
            if verbosity: print(' Seq  = %s\n P    = %1.2e\n' % (X,P))
            if verbosity >= 2: print_trellis(T, X)
            


    # FORWARD or BACKWARD
    elif cmd in ['forward','backward']:
        if cmd == 'forward':
            algorithm = forward
        elif cmd == 'backward':
            algorithm = backward

        for j,X in enumerate(set_X): # For every sequence:
            # Calculate the Forward/Backward probability and corresponding matrix
            P, T = algorithm(X,A,E)

            # Save and/or print relevant output
            label = labels[j]
            save('%s.matrix' % label, serialize(T,X))
            save('%s.p' % label, '%1.2e' % P)
            if verbosity >= 2:
                print('\n>%s\n P = %1.2e\n' % (label,P))
                print_trellis(T, X)
            elif verbosity: print('>%-10s\tP = %1.2e' % (label,P))



    # BAUM-WELCH TRAINING
    elif cmd == 'baumwelch':
        # Initialize
        i = 1
        i_max = args.max_iter
        threshold = args.conv_thresh

        current_SLL, A, E = baumwelch(set_X,A,E)
        if verbosity: print('Iteration %i, prior SLL = %1.2e' % (i,current_SLL))
        if verbosity >= 2: print_params(A,E)
        
        last_SLL = current_SLL - threshold - 1 # Iterate at least once

        # Iterate until convergence or limit
        while i < i_max and current_SLL - last_SLL > threshold:
            i += 1
            last_SLL = current_SLL

            # Calculate the Sum Log-Likelihood of X given A and E,
            # and update the estimates (posteriors) for A and E.
            current_SLL, A, E = baumwelch(set_X,A,E)

            if verbosity: print('Iteration %i, prior SLL = %1.2e' % (i,current_SLL))
            if verbosity >= 2: print_params(A,E)

        converged = current_SLL - last_SLL <= threshold
        final_SLL = sum([log10(forward(X,A,E)[0]) if forward(X,A,E)[0] > 0 else 0 for X in set_X])
        # Save and/or print relevant output
        save('SLL','%1.2e\t%i\t%s' % (final_SLL, i, converged))
        save('posterior_A',serialize(A))
        save('posterior_E',serialize(E))
        if verbosity: print('========================================\n')

        if converged:
            print('Converged after %i iterations.' % i)
        else:
            print('Failed to converge after %i iterations.' % i_max)

        if verbosity:
            print('Final SLL: %1.2e' % final_SLL)
            print('Final parameters:')
            print_params(A,E)



if __name__ == '__main__':
	main()