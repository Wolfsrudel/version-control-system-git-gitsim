from manim import *
import git, sys, numpy

class GitSimBaseCommand():

    def __init__(self, scene):
        self.scene = scene
        self.init_repo()

        self.drawnCommits = {}
        self.drawnRefs = {}
        self.commits = []
        self.zoomOuts = 0 
        self.toFadeOut = Group()
        self.trimmed = False
        self.prevRef = None
        self.topref = None
        self.maxrefs = None
        self.i = 0

        self.logo = ImageMobject(self.scene.args.logo)
        self.logo.width = 3

    def init_repo(self):
        try:
            self.repo = git.Repo(search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError:
            print("git-sim error: No Git repository found at current path.")
            sys.exit(1)

    def execute(self):
        print("Simulating: git " + self.scene.args.subcommand)
        self.show_intro()
        self.get_commits()
        self.fadeout()
        self.show_outro()

    def parse_commits(self, commit, prevCircle=None):
        if ( self.i < self.scene.args.commits and commit in self.commits ):
            commitId, circle, arrow = self.draw_commit(commit, prevCircle)
            self.draw_head(commit, commitId)
            self.draw_branch(commit)
            self.draw_tag(commit)
            self.draw_arrow(prevCircle, arrow)

            if self.i < len(self.commits)-1:
                self.i += 1
                self.parse_commits(self.commits[self.i], circle)

    def show_intro(self):
        if ( self.scene.args.show_intro ):
            self.scene.add(self.logo)

            initialCommitText = Text(self.scene.args.title, font="Monospace", font_size=36, color=self.scene.fontColor).to_edge(UP, buff=1)
            self.scene.add(initialCommitText)
            self.scene.wait(2)
            self.scene.play(FadeOut(initialCommitText))
            self.scene.play(self.logo.animate.scale(0.25).to_edge(UP, buff=0).to_edge(RIGHT, buff=0))
    
            self.scene.camera.frame.save_state()
            self.scene.play(FadeOut(self.logo))

        else:
            self.logo.scale(0.25).to_edge(UP, buff=0).to_edge(RIGHT, buff=0)
            self.scene.camera.frame.save_state()        

    def show_outro(self):
        if ( self.scene.args.show_outro ):

            self.scene.play(Restore(self.scene.camera.frame))

            self.scene.play(self.logo.animate.scale(4).set_x(0).set_y(0))

            outroTopText = Text(self.scene.args.outro_top_text, font="Monospace", font_size=36, color=self.scene.fontColor).to_edge(UP, buff=1)
            self.scene.play(AddTextLetterByLetter(outroTopText))

            outroBottomText = Text(self.scene.args.outro_bottom_text, font="Monospace", font_size=36, color=self.scene.fontColor).to_edge(DOWN, buff=1)
            self.scene.play(AddTextLetterByLetter(outroBottomText))

            self.scene.wait(3)

    def fadeout(self):
        self.scene.wait(3)
        self.scene.play(FadeOut(self.toFadeOut), run_time=1/self.scene.args.speed)

    def get_commits(self):
        try:
            self.commits = list(self.repo.iter_commits('HEAD~5...HEAD'))

        except git.exc.GitCommandError:
            print("git-sim error: No commits in current Git repository.")
            sys.exit(1)

    def get_centers(self):
        centers = []
        for commit in self.drawnCommits.values():
            centers.append(commit.get_center())
        return centers

    def draw_commit(self, commit, prevCircle):
        if ( len(commit.parents) <= 1 ):
            commitFill = RED 
        else:
            commitFill = GRAY

        circle = Circle(stroke_color=commitFill, fill_color=commitFill, fill_opacity=0.25)
        circle.height = 1 

        if prevCircle:
            circle.next_to(prevCircle, RIGHT, buff=1.5)

        start = prevCircle.get_center() if prevCircle else LEFT
        end = circle.get_center()

        arrow = Arrow(start, end, color=self.scene.fontColor)
        length = numpy.linalg.norm(start-end) - ( 1.5 if start[1] == end[1] else 3  )
        arrow.set_length(length)

        commitId, commitMessage = self.build_commit_id_and_message(commit)
        commitId.next_to(circle, UP)

        message = Text('\n'.join(commitMessage[j:j+20] for j in range(0, len(commitMessage), 20))[:100], font="Monospace", font_size=14, color=self.scene.fontColor).next_to(circle, DOWN)

        self.scene.play(self.scene.camera.frame.animate.move_to(circle.get_center()), Create(circle), AddTextLetterByLetter(commitId), AddTextLetterByLetter(message), run_time=1/self.scene.args.speed)
        self.drawnCommits[commit.hexsha] = circle

        self.toFadeOut.add(circle, commitId, message)
        self.prevRef = commitId

        return commitId, circle, arrow

    def build_commit_id_and_message(self, commit):
        commitId = Text(commit.hexsha[0:6], font="Monospace", font_size=20, color=self.scene.fontColor)
        commitMessage = commit.message[:40].replace("\n", " ")
        return commitId, commitMessage

    def draw_head(self, commit, commitId):
        if ( commit.hexsha == self.repo.head.commit.hexsha ):
            headbox = Rectangle(color=BLUE, fill_color=BLUE, fill_opacity=0.25)
            headbox.width = 1 
            headbox.height = 0.4 
            headbox.next_to(commitId, UP) 
            headText = Text("HEAD", font="Monospace", font_size=20, color=self.scene.fontColor).move_to(headbox.get_center())

            head = VGroup(headbox, headText)

            self.scene.play(Create(head), run_time=1/self.scene.args.speed)
            self.toFadeOut.add(head)
            self.drawnRefs["HEAD"] = head
            self.prevRef = head

            if self.i == 0:
                self.topref = self.prevRef

    def draw_branch(self, commit):
        x = 0 
        for branch in self.repo.heads:

            if self.maxrefs and len(self.drawnRefs) >= self.maxrefs:
                return

            if ( commit.hexsha == branch.commit.hexsha and branch.name == self.repo.active_branch.name ):
                branchText = Text(branch.name, font="Monospace", font_size=20, color=self.scene.fontColor)
                branchRec = Rectangle(color=GREEN, fill_color=GREEN, fill_opacity=0.25, height=0.4, width=branchText.width+0.25)

                branchRec.next_to(self.prevRef, UP) 
                branchText.move_to(branchRec.get_center())

                fullbranch = VGroup(branchRec, branchText)

                self.prevRef = fullbranch

                self.scene.play(Create(fullbranch), run_time=1/self.scene.args.speed)
                self.toFadeOut.add(branchRec, branchText)
                self.drawnRefs[branch.name] = fullbranch

                x += 1

                if self.i == 0:
                    self.topref = self.prevRef

    def draw_tag(self, commit):
        x = 0 
        for tag in self.repo.tags:

            if self.maxrefs and len(self.drawnRefs) >= self.maxrefs:
                return

            if ( commit.hexsha == tag.commit.hexsha ):
                tagText = Text(tag.name, font="Monospace", font_size=20, color=self.scene.fontColor)
                tagRec = Rectangle(color=YELLOW, fill_color=YELLOW, fill_opacity=0.25, height=0.4, width=tagText.width+0.25)

                tagRec.next_to(self.prevRef, UP) 
                tagText.move_to(tagRec.get_center())

                self.prevRef = tagRec

                self.scene.play(Create(tagRec), Create(tagText), run_time=1/self.scene.args.speed)
                self.toFadeOut.add(tagRec, tagText)

                x += 1

                if self.i == 0:
                    self.topref = self.prevRef

    def draw_arrow(self, prevCircle, arrow):
        if ( prevCircle ):
            self.scene.play(Create(arrow), run_time=1/self.scene.args.speed)
            self.toFadeOut.add(arrow)

    def recenter_frame(self):
        self.scene.play(self.scene.camera.frame.animate.move_to(self.toFadeOut.get_center()), run_time=1/self.scene.args.speed)

    def scale_frame(self):
        self.scene.play(self.scene.camera.frame.animate.scale_to_fit_width(self.toFadeOut.get_width()*1.1), run_time=1/self.scene.args.speed)
        if ( self.toFadeOut.get_height() >= self.scene.camera.frame.get_height() ):
            self.scene.play(self.scene.camera.frame.animate.scale_to_fit_height(self.toFadeOut.get_height()*1.25), run_time=1/self.scene.args.speed)

    def vsplit_frame(self):
        self.scene.play(self.scene.camera.frame.animate.scale_to_fit_height(self.scene.camera.frame.get_height()*2))

        try:
            self.scene.play(self.toFadeOut.animate.align_to(self.scene.camera.frame, UP).shift(DOWN*0.75))
        except ValueError:
            pass

    def setup_and_draw_zones(self, upshift=2.6, first_column_name="Untracked files"):
        horizontal = Line((self.scene.camera.frame.get_left()[0], self.scene.camera.frame.get_center()[1], 0), (self.scene.camera.frame.get_right()[0], self.scene.camera.frame.get_center()[1], 0), color=self.scene.fontColor).shift(UP*2.5)
        horizontal2 = Line((self.scene.camera.frame.get_left()[0], self.scene.camera.frame.get_center()[1], 0), (self.scene.camera.frame.get_right()[0], self.scene.camera.frame.get_center()[1], 0), color=self.scene.fontColor).shift(UP*1.5)
        vert1 = DashedLine((self.scene.camera.frame.get_left()[0], self.scene.camera.frame.get_bottom()[1], 0), (self.scene.camera.frame.get_left()[0], horizontal.get_start()[1], 0), dash_length=0.2, color=self.scene.fontColor).shift(RIGHT*6.5)
        vert2 = DashedLine((self.scene.camera.frame.get_right()[0], self.scene.camera.frame.get_bottom()[1], 0), (self.scene.camera.frame.get_right()[0], horizontal.get_start()[1], 0), dash_length=0.2, color=self.scene.fontColor).shift(LEFT*6.5)

        deletedText = Text(first_column_name, font="Monospace", font_size=28, color=self.scene.fontColor).align_to(self.scene.camera.frame, LEFT).shift(RIGHT*0.65).shift(UP*upshift)
        workingdirectoryText = Text("Working directory modifications", font="Monospace", font_size=28, color=self.scene.fontColor).move_to(self.scene.camera.frame.get_center()).align_to(deletedText, UP)
        stagingareaText = Text("Staged changes", font="Monospace", font_size=28, color=self.scene.fontColor).align_to(self.scene.camera.frame, RIGHT).shift(LEFT*1.65).align_to(deletedText, UP)

        self.toFadeOut.add(horizontal, horizontal2, vert1, vert2, deletedText, workingdirectoryText, stagingareaText)
        self.scene.play(Create(horizontal), Create(horizontal2), Create(vert1), Create(vert2), AddTextLetterByLetter(deletedText), AddTextLetterByLetter(workingdirectoryText), AddTextLetterByLetter(stagingareaText)) 

        deletedFileNames = set()
        workingFileNames = set()
        stagedFileNames = set()

        self.populate_zones(deletedFileNames, workingFileNames, stagedFileNames)

        deletedFiles = VGroup()
        workingFiles = VGroup()
        stagedFiles = VGroup()

        for i, f in enumerate(deletedFileNames):
            deletedFiles.add(Text(f, font="Monospace", font_size=24, color=self.scene.fontColor).move_to((deletedText.get_center()[0], horizontal2.get_center()[1], 0)).shift(DOWN*0.5*(i+1)))

        for j, f in enumerate(workingFileNames):
            workingFiles.add(Text(f, font="Monospace", font_size=24, color=self.scene.fontColor).move_to((workingdirectoryText.get_center()[0], horizontal2.get_center()[1], 0)).shift(DOWN*0.5*(j+1)))

        for h, f in enumerate(stagedFileNames):
            stagedFiles.add(Text(f, font="Monospace", font_size=24, color=self.scene.fontColor).move_to((stagingareaText.get_center()[0], horizontal2.get_center()[1], 0)).shift(DOWN*0.5*(h+1)))

        if len(deletedFiles):
            self.scene.play(*[AddTextLetterByLetter(d) for d in deletedFiles])

        if len(workingFiles):
            self.scene.play(*[AddTextLetterByLetter(w) for w in workingFiles])

        if len(stagedFiles):
            self.scene.play(*[AddTextLetterByLetter(s) for s in stagedFiles])

        self.toFadeOut.add(deletedFiles, workingFiles, stagedFiles)

    def populate_zones(self, deletedFileNames, workingFileNames, stagedFileNames):

        for x in self.repo.index.diff(None):
            workingFileNames.add(x.a_path)

        for y in self.repo.index.diff("HEAD"):
            stagedFileNames.add(y.a_path)

        for z in self.repo.untracked_files:
            deletedFileNames.add(z)

    def center_frame_on_start_commit(self):
        self.scene.play(self.scene.camera.frame.animate.move_to(self.drawnCommits[self.commits[0].hexsha].get_center()))

    def reset_head_branch(self, hexsha):
        self.scene.play(self.drawnRefs["HEAD"].animate.move_to((self.drawnCommits[hexsha].get_center()[0], self.drawnRefs["HEAD"].get_center()[1], 0)),
                        self.drawnRefs[self.repo.active_branch.name].animate.move_to((self.drawnCommits[hexsha].get_center()[0], self.drawnRefs[self.repo.active_branch.name].get_center()[1], 0)))