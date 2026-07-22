# 1. Open a RFC PR that proposes to merge the new RFC document.
    - Updates can be made to the RFC document though the comments and discussion surrounding implementaiton options remain in the PR.
    - The PR is approved (but not merged) or rejected thus reflecting the decision to implement the change suggested in the RFC.

# 2. Open a Impl PR that performs the implementation based on the RFC PR.
    - The RPC PR with comments is reviewed, clarifying questions are asked in the RFC PR and that PR can be changed from approved to requires more information if necessary.
    - Implementation begins and ends with an Impl PR to merge new branch into main.

# 3. Details

## 3.1 This puts the RFC under review to determine if we want to move to implemetation or not.

    git branch create rfc/010-run-cancelled-enum
    git branch checkout rfc/010-run-cancelled-enum
    git add 010-run-cancelled-enum.md
    git commit 010-run-canceled-enum.md
    git push rfc/010-run-cancelled-enum 
    git pr create message is the contents of the RFC file.

### This took place using an openclaude agent and the most powerful model.
LET THE COMMENTING BEGIN. AFTER SOME ROUNDS OF COMMENTING, APPROVE OR REJECT THE RFC PR (BUT DO NOT MERGE INTO MAIN YET, THE IMPL AGENT MAY REQUIRE ADDITIONAL CLARRIFICATION.

### After one or two rounds of comments, The decision to implement or not is made and reflected in the approval decision. If the decision to implment is made, I move from openclaude agents using the best model to cursor where I have auto selected for the model choice.

### Comments concering the RFC are posted in the PR. Solution are ultimately proposed as coments in the PR, and if the decision is made to to proceed with the change, the changes take place on a new branch off of main named consistently with the RFC PR by appending -impl to the new branch name.

## 3.2 Implementation of Changes.
When the changes are done, the Impl PR is reviewed by reviewers, and if approved, are merged into main.

### 3.2 Resolution of RFC005 for PR4

### 3.2 This took place in Cursor Agent 1. The Design Review

Resolution of RFC005 for PR4. Read PR4 at github.com/brettin/ARIA. Read all the comments in the PR. They contain implementation guidance. Are there any open questions? What are the pros and cons to the different approaches. Do you disagree with the implementation plan? Draft the “Recommended approach” subsection text for RFC 001. Keep it short. Any additional questions go here.

--do a turn--

We will update the platform and clients in a different context. We should note when the platform and client will need updating. Please post any additional clarifying questions based to PR4. Once those are answered, I will ask an implementation agent to read the PR and all of it's comments and implement the changes.


### 3.3 RFC005 implementation for PR4
### This took place in Cursor Agent 2. The Implementation

RFC005 implementation for PR4. Read PR4 at github.com/brettin/ARIA. Read all the comments in the PR. They contain implementation guidance. Create a new branch, and implement those changes. The new branch should be off of main. We will update the platform and clients in a different context. I would like to know the pros and cons of each recommended disposition. Commit and push to remote, but don't open a PR yet.

--do a turn-- Human review of pros and cons.

Let's create a pull request for the rfc005 impl.

--do a turn-- Wait on Human PR approval.

The pull request has been reviewed, approved, and merged into main. Then, let's bump the version tag on main assocatiated with the merge and be done.


## Two skills derived from RFC001 and RFC005
Resolve RFC.
Implement Changes.