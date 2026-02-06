"""
検定試験練習問題バンク
各試験の出題形式・トピック・難易度に忠実な問題群
"""

import random

# ====================================================================
# TOEFL ITP
# ====================================================================

TOEFL_ITP_LISTENING = {
    "short_conversation": {
        "easy": [
            {
                "dialogue": "W: Have you signed up for Professor Miller's linguistics seminar yet?\nM: I tried to, but it was already full. I'm on the waiting list now.",
                "question": "What does the man mean?",
                "choices": [
                    "A) He is enrolled in the seminar.",
                    "B) He was unable to register because the class is full.",
                    "C) He doesn't want to take the seminar.",
                    "D) He forgot to sign up for the class."
                ],
                "correct": "B",
                "explanation": "男性は登録しようとしたが定員で、ウェイティングリストに入ったと言っています。Bが正解。",
                "skill_focus": "大学の履修登録に関する会話"
            },
            {
                "dialogue": "M: Could you tell me where the chemistry lab is?\nW: It's in the science building, room 204. Go down this hall and take the elevator to the second floor.",
                "question": "Where does the woman direct the man?",
                "choices": [
                    "A) To the library on the first floor",
                    "B) To room 204 in the science building",
                    "C) To the professor's office",
                    "D) To the main entrance of campus"
                ],
                "correct": "B",
                "explanation": "女性は「science buildingの204号室」と案内しています。Bが正解。",
                "skill_focus": "キャンパス内の場所案内"
            },
            {
                "dialogue": "W: I'm not sure whether to take biology or geology to fulfill my science requirement.\nM: Why don't you sit in on both classes this week and see which one you prefer?",
                "question": "What does the man suggest the woman do?",
                "choices": [
                    "A) Take both classes at the same time",
                    "B) Ask an advisor for help",
                    "C) Attend both classes before deciding",
                    "D) Choose biology because it's easier"
                ],
                "correct": "C",
                "explanation": "男性は「両方の授業を聴講してから決めたら」と提案しています。sit in on = 聴講する。Cが正解。",
                "skill_focus": "提案・助言の理解"
            },
        ],
        "medium": [
            {
                "dialogue": "M: I've been struggling with this organic chemistry assignment all weekend.\nW: You should try the tutoring center in the library. They have graduate students who specialize in chemistry.",
                "question": "What does the woman suggest?",
                "choices": [
                    "A) The man should drop the chemistry course.",
                    "B) The man should seek help at the tutoring center.",
                    "C) The man should study with other undergraduates.",
                    "D) The man should ask the professor directly."
                ],
                "correct": "B",
                "explanation": "女性は図書館のチュータリングセンターで化学専門の大学院生に教えてもらうことを勧めています。Bが正解。",
                "skill_focus": "キャンパスサービスに関する助言"
            },
            {
                "dialogue": "W: The results of our experiment don't match the theoretical predictions at all.\nM: That could actually be more interesting than if they had matched. Let's discuss it with Dr. Hansen.",
                "question": "What can be inferred about the man?",
                "choices": [
                    "A) He is disappointed by the experimental results.",
                    "B) He thinks the unexpected results may be scientifically valuable.",
                    "C) He wants to repeat the experiment.",
                    "D) He believes they made an error in the procedure."
                ],
                "correct": "B",
                "explanation": "男性は「一致しなかった方がむしろ面白いかもしれない」と言い、教授と議論することを提案しています。予想外の結果に科学的価値を見出しているのでBが正解。",
                "skill_focus": "含意・推論の理解"
            },
            {
                "dialogue": "M: Did you hear that the university is cutting funding for the arts program?\nW: Yes, and a group of students is organizing a petition to present to the administration. I think I'll sign it.",
                "question": "What will the woman probably do?",
                "choices": [
                    "A) She will transfer to another university.",
                    "B) She will support the petition against the funding cuts.",
                    "C) She will apply for a scholarship.",
                    "D) She will meet with the university president."
                ],
                "correct": "B",
                "explanation": "女性は「署名しようと思う」と言っているので、資金削減に反対する請願に賛同するBが正解。",
                "skill_focus": "今後の行動の予測"
            },
            {
                "dialogue": "W: I thought the deadline for the research proposal was next Friday.\nM: It was, but Professor Clark moved it up to this Wednesday because of the conference schedule.",
                "question": "What does the man mean?",
                "choices": [
                    "A) The deadline has been extended.",
                    "B) The deadline is still next Friday.",
                    "C) The deadline has been moved to an earlier date.",
                    "D) The conference has been cancelled."
                ],
                "correct": "C",
                "explanation": "moved it up は「前倒しにした」という意味。金曜日から水曜日に繰り上がったのでCが正解。",
                "skill_focus": "イディオム・スケジュール変更の理解"
            },
        ],
        "hard": [
            {
                "dialogue": "M: Professor Williams' lecture on plate tectonics was so dense. I could barely keep up with my notes.\nW: I know what you mean. But if you compare it with the corresponding chapter in the textbook, a lot of the terminology starts to make more sense in context.",
                "question": "What does the woman imply?",
                "choices": [
                    "A) The textbook is poorly written.",
                    "B) Reading the textbook alongside the lecture notes will aid comprehension.",
                    "C) The lecture was easier to understand than the textbook.",
                    "D) The man should ask for simpler explanations."
                ],
                "correct": "B",
                "explanation": "女性は教科書の該当章と照らし合わせれば専門用語が理解しやすくなると助言しています。Bが正解。",
                "skill_focus": "学習方法に関する含意"
            },
            {
                "dialogue": "W: The anthropology department is hosting a symposium on indigenous languages this semester. They've invited scholars from six different countries.\nM: That sounds fascinating. Do you know if it's open to students outside the department?",
                "question": "What does the man want to know?",
                "choices": [
                    "A) Whether the symposium has been cancelled",
                    "B) How many countries will be represented",
                    "C) Whether non-anthropology students can attend",
                    "D) When the symposium will take place"
                ],
                "correct": "C",
                "explanation": "男性は「学部外の学生も参加できるか」を尋ねています。outside the department = 学部外。Cが正解。",
                "skill_focus": "具体的な質問内容の特定"
            },
        ],
    },
    "lecture": {
        "medium": [
            {
                "dialogue": "Today I want to discuss the concept of ecological succession—the process by which the structure of a biological community evolves over time. There are two main types: primary succession and secondary succession. Primary succession occurs in lifeless areas where there is no soil, such as after a volcanic eruption or glacial retreat. Pioneer species, typically lichens and mosses, colonize the bare rock first. Over time, they break down the rock surface, creating a thin layer of soil. This allows grasses and small shrubs to take root, which are eventually replaced by larger plants and trees. This entire process can take hundreds or even thousands of years.",
                "question": "According to the professor, what is the role of pioneer species?",
                "choices": [
                    "A) They prevent other species from growing.",
                    "B) They break down rock to create soil for later species.",
                    "C) They appear only after trees are established.",
                    "D) They grow rapidly in fertile soil."
                ],
                "correct": "B",
                "explanation": "教授はパイオニア種（地衣類や苔）が岩石を分解して薄い土壌層を作り、後の植物の生育を可能にすると説明しています。Bが正解。",
                "skill_focus": "講義の詳細理解"
            },
        ],
        "hard": [
            {
                "dialogue": "In today's lecture on cognitive psychology, I'd like to examine the concept of working memory. Alan Baddeley's model, proposed in 1974 and revised in 2000, suggests that working memory isn't a single system. Rather, it consists of multiple components: the phonological loop, which handles verbal and acoustic information; the visuospatial sketchpad, which processes visual and spatial data; and the central executive, which directs attention and coordinates the other components. Baddeley later added a fourth component—the episodic buffer—which integrates information from different sources into coherent episodes. This model helps explain why we can, for instance, listen to a lecture while taking notes—these tasks rely on different subsystems.",
                "question": "Why did Baddeley add the episodic buffer to his model?",
                "choices": [
                    "A) To replace the phonological loop",
                    "B) To explain how different types of information are combined",
                    "C) To describe long-term memory storage",
                    "D) To account for visual processing"
                ],
                "correct": "B",
                "explanation": "エピソードバッファは「異なるソースからの情報を一貫したエピソードに統合する」ために追加されました。Bが正解。",
                "skill_focus": "学術理論の構造理解"
            },
        ],
    },
}


TOEFL_ITP_STRUCTURE = {
    "sentence_completion": {
        "easy": [
            {
                "question_type": "sentence_completion",
                "sentence": "The professor suggested that the student ______ the assignment by Friday.",
                "choices": ["A) complete", "B) completes", "C) completed", "D) completing"],
                "correct": "A",
                "explanation": "suggest/recommend/insist that の後は仮定法現在（原形）を使います。主語が三人称単数でも原形。",
                "grammar_point": "仮定法現在 (subjunctive mood)"
            },
            {
                "question_type": "sentence_completion",
                "sentence": "The number of international students at this university ______ increased significantly over the past decade.",
                "choices": ["A) have", "B) has", "C) are", "D) were"],
                "correct": "B",
                "explanation": "The number of ~ は単数扱いなので has が正解。A number of ~ なら複数扱い。",
                "grammar_point": "主語と動詞の一致"
            },
            {
                "question_type": "sentence_completion",
                "sentence": "______ the experiment was conducted carefully, the results were inconclusive.",
                "choices": ["A) Because of", "B) Despite", "C) Although", "D) In spite"],
                "correct": "C",
                "explanation": "後に完全な文(SV)が続くので接続詞Althoughが正解。Despite/In spite ofの後は名詞。",
                "grammar_point": "譲歩の接続詞と前置詞"
            },
        ],
        "medium": [
            {
                "question_type": "sentence_completion",
                "sentence": "Not until the late nineteenth century ______ the cause of malaria.",
                "choices": ["A) scientists discovered", "B) did scientists discover", "C) scientists did discover", "D) had scientists discover"],
                "correct": "B",
                "explanation": "Not until で始まる文では倒置が起こります。did scientists discover が正しい語順。",
                "grammar_point": "否定語句による倒置"
            },
            {
                "question_type": "sentence_completion",
                "sentence": "Had the researchers ______ the variables more carefully, the results might have been different.",
                "choices": ["A) control", "B) controlled", "C) controlling", "D) to control"],
                "correct": "B",
                "explanation": "Had + S + p.p. は仮定法過去完了の倒置形。If the researchers had controlled の省略形。",
                "grammar_point": "仮定法過去完了の倒置"
            },
            {
                "question_type": "sentence_completion",
                "sentence": "The archaeological site, ______ was discovered in 1922, has yielded thousands of artifacts.",
                "choices": ["A) that", "B) which", "C) where", "D) what"],
                "correct": "B",
                "explanation": "コンマ付きの非制限用法の関係代名詞にはwhichを使います。thatは非制限用法では使えません。",
                "grammar_point": "関係代名詞の制限・非制限用法"
            },
        ],
        "hard": [
            {
                "question_type": "sentence_completion",
                "sentence": "So rapidly ______ that scientists are struggling to document them all before they disappear.",
                "choices": [
                    "A) species are becoming extinct",
                    "B) are species becoming extinct",
                    "C) species becoming extinct",
                    "D) do species becoming extinct"
                ],
                "correct": "B",
                "explanation": "So + 副詞で始まる文では倒置が起こります。are species becoming extinct が正しい語順。",
                "grammar_point": "So/Such による倒置構文"
            },
            {
                "question_type": "sentence_completion",
                "sentence": "The professor requires that every thesis ______ peer-reviewed before submission to the committee.",
                "choices": ["A) is", "B) be", "C) will be", "D) being"],
                "correct": "B",
                "explanation": "require that の後は仮定法現在。受動態の仮定法現在は be + p.p.（be reviewed）。",
                "grammar_point": "仮定法現在の受動態"
            },
        ],
    },
    "error_identification": {
        "easy": [
            {
                "question_type": "error_identification",
                "sentence": "The team (A)have been (B)working on the project (C)since (D)three months.",
                "choices": ["A) have", "B) working", "C) since", "D) three months"],
                "correct": "D",
                "explanation": "sinceの後は時点（例: last March）が来ます。期間にはforを使うので、for three monthsが正しい。",
                "grammar_point": "since と for の使い分け"
            },
            {
                "question_type": "error_identification",
                "sentence": "Neither the students (A)nor the professor (B)were (C)satisfied with (D)the outcome of the experiment.",
                "choices": ["A) nor", "B) were", "C) satisfied with", "D) the outcome"],
                "correct": "B",
                "explanation": "neither A nor B では動詞はBに一致します。the professor は単数なので was が正しい。",
                "grammar_point": "相関接続詞と主語動詞の一致"
            },
        ],
        "medium": [
            {
                "question_type": "error_identification",
                "sentence": "The (A)discovery of antibiotics (B)have had a (C)profound impact on (D)modern medicine.",
                "choices": ["A) discovery", "B) have had", "C) profound", "D) modern medicine"],
                "correct": "B",
                "explanation": "主語はThe discovery（単数）なので、has hadが正しい。of antibioticsは修飾語句で主語に影響しない。",
                "grammar_point": "修飾語句に惑わされない主語動詞の一致"
            },
            {
                "question_type": "error_identification",
                "sentence": "(A)Comparing with other primates, humans have a (B)significantly larger (C)prefrontal cortex relative to (D)overall brain size.",
                "choices": ["A) Comparing with", "B) significantly larger", "C) prefrontal cortex", "D) overall brain size"],
                "correct": "A",
                "explanation": "humansは「比較される側」なので、過去分詞Compared withが正しい。主語と分詞の関係に注意。",
                "grammar_point": "分詞構文の能動・受動"
            },
        ],
        "hard": [
            {
                "question_type": "error_identification",
                "sentence": "The data (A)collected during the field study (B)suggests that the ecosystem is (C)more fragile (D)than previously believing.",
                "choices": ["A) collected", "B) suggests", "C) more fragile", "D) than previously believing"],
                "correct": "D",
                "explanation": "than previously believed（過去分詞）が正しい。it was believed の省略形。believingは不可。",
                "grammar_point": "比較構文における省略と分詞"
            },
        ],
    },
}


TOEFL_ITP_READING = {
    "medium": [
        {
            "passage": "The development of the telegraph in the 1830s and 1840s revolutionized long-distance communication. Before its invention, messages could only travel as fast as the fastest horse or ship. Samuel Morse, an American inventor and painter, developed the most commercially successful version of the telegraph along with the Morse code system for encoding messages. By 1866, a transatlantic telegraph cable connected North America and Europe, reducing the time to send a message across the Atlantic from about ten days by ship to mere minutes. The telegraph's impact on journalism was equally transformative. News agencies such as the Associated Press were founded to share the costs of telegraph transmissions, and newspapers could for the first time report on events happening across the country on the same day they occurred. The telegraph also played a critical role in the expansion of railroads, as it allowed for the coordination of train schedules across vast distances, greatly improving both safety and efficiency.",
            "questions": [
                {
                    "question": "What is the main topic of the passage?",
                    "choices": [
                        "A) The biography of Samuel Morse",
                        "B) The impact of the telegraph on communication and society",
                        "C) The history of transatlantic shipping",
                        "D) The founding of the Associated Press"
                    ],
                    "correct": "B",
                    "explanation": "パッセージ全体が電信の発明と、それがジャーナリズム・鉄道など社会に与えた影響について述べています。Bが正解。",
                    "skill_focus": "主旨把握"
                },
                {
                    "question": "According to the passage, how did the telegraph affect journalism?",
                    "choices": [
                        "A) It made newspapers more expensive.",
                        "B) It enabled same-day reporting of distant events.",
                        "C) It replaced newspapers entirely.",
                        "D) It reduced the number of journalists needed."
                    ],
                    "correct": "B",
                    "explanation": "「新聞が初めて同日中に国中の出来事を報道できるようになった」と述べられています。Bが正解。",
                    "skill_focus": "詳細理解"
                },
            ]
        },
    ],
    "hard": [
        {
            "passage": "Photosynthesis, the process by which green plants and certain other organisms convert light energy into chemical energy, is arguably the most important biochemical process on Earth. During photosynthesis, carbon dioxide and water are transformed into glucose and oxygen through a series of complex reactions that occur in two main stages. The light-dependent reactions, which take place in the thylakoid membranes of the chloroplast, capture solar energy and use it to produce ATP and NADPH. These energy carriers then drive the light-independent reactions, also known as the Calvin cycle, which occur in the stroma of the chloroplast. In the Calvin cycle, carbon dioxide is fixed into organic molecules through a process called carbon fixation, catalyzed by the enzyme RuBisCO. Interestingly, RuBisCO is the most abundant protein on Earth, reflecting the enormous scale at which photosynthesis operates globally. Recent research has focused on improving the efficiency of RuBisCO, which also catalyzes a wasteful side reaction called photorespiration, in an effort to enhance crop yields to meet growing global food demands.",
            "questions": [
                {
                    "question": "The word 'fixed' in the passage is closest in meaning to:",
                    "choices": [
                        "A) repaired",
                        "B) attached",
                        "C) incorporated into a stable form",
                        "D) concentrated"
                    ],
                    "correct": "C",
                    "explanation": "carbon fixation における fix は「安定した形に取り込む」という意味。CO2が有機分子に変換される過程を指します。Cが正解。",
                    "skill_focus": "文脈からの語彙推測"
                },
                {
                    "question": "Why is improving RuBisCO efficiency a focus of current research?",
                    "choices": [
                        "A) To reduce the amount of oxygen produced",
                        "B) To increase crop production for the growing population",
                        "C) To eliminate the Calvin cycle",
                        "D) To replace photosynthesis with artificial processes"
                    ],
                    "correct": "B",
                    "explanation": "RuBisCOの効率改善は「増大する世界の食糧需要に対応するため作物の収量を向上させる」目的と述べられています。Bが正解。",
                    "skill_focus": "目的・理由の理解"
                },
            ]
        },
    ],
}


# ====================================================================
# TOEIC L&R
# ====================================================================

TOEIC_LISTENING = {
    "part2": {
        "easy": [
            {
                "dialogue": "W: When is the next staff meeting?",
                "question": "Choose the best response.",
                "choices": [
                    "A) It's in conference room B.",
                    "B) It's scheduled for Thursday at 2 PM.",
                    "C) I'll meet you at the lobby."
                ],
                "correct": "B",
                "explanation": "When（いつ）に対して時間を答えているBが正解。Aは場所、Cは関係のない応答。",
                "skill_focus": "疑問詞疑問文への応答"
            },
            {
                "dialogue": "M: Could you send me the quarterly sales report?",
                "question": "Choose the best response.",
                "choices": [
                    "A) I'll e-mail it to you this afternoon.",
                    "B) The store is on the third floor.",
                    "C) I reported for duty on Monday."
                ],
                "correct": "A",
                "explanation": "依頼に対して「今日の午後メールします」と応じているAが正解。",
                "skill_focus": "依頼への応答"
            },
        ],
        "medium": [
            {
                "dialogue": "W: Hasn't the shipment from the supplier arrived yet?",
                "question": "Choose the best response.",
                "choices": [
                    "A) No, it's been delayed due to a customs issue.",
                    "B) Yes, I'd like to ship it tomorrow.",
                    "C) The supplier is located downtown."
                ],
                "correct": "A",
                "explanation": "否定疑問文に対して「まだ届いていない。税関の問題で遅延」と答えるAが正解。",
                "skill_focus": "否定疑問文への応答"
            },
        ],
    },
    "part3": {
        "medium": [
            {
                "dialogue": "W: I noticed the client presentation has been moved to Friday. Do we have enough time to prepare?\nM: I think so, but we'll need to finalize the budget figures by Wednesday at the latest.\nW: I'll check with accounting and get those numbers to you by tomorrow afternoon.",
                "question": "What does the woman offer to do?",
                "choices": [
                    "A) Reschedule the presentation",
                    "B) Contact the accounting department",
                    "C) Prepare the presentation slides",
                    "D) Meet with the client directly"
                ],
                "correct": "B",
                "explanation": "女性は「経理に確認して明日の午後までに数字を渡す」と申し出ています。Bが正解。",
                "skill_focus": "ビジネス会話の行動予測"
            },
        ],
        "hard": [
            {
                "dialogue": "M: We've received several complaints from customers about the new online ordering system.\nW: What kind of complaints? Is it a technical issue or a design problem?\nM: Mostly about the checkout process. Customers are saying it takes too many steps to complete a purchase.\nW: Let's set up a meeting with the development team. We should streamline the process before the holiday shopping season.",
                "question": "What problem are the speakers discussing?",
                "choices": [
                    "A) Declining sales during the holiday season",
                    "B) A complicated online checkout process",
                    "C) Customer complaints about product quality",
                    "D) A shortage of development staff"
                ],
                "correct": "B",
                "explanation": "顧客の苦情は「チェックアウトプロセスのステップが多すぎる」ことです。Bが正解。",
                "skill_focus": "問題点の特定"
            },
        ],
    },
    "part4": {
        "medium": [
            {
                "dialogue": "Attention all employees. Due to the scheduled maintenance of the building's electrical system, the office will be closed next Monday, March 15th. Please save all your digital files to the cloud server by Friday evening, as local servers will be shut down during the maintenance period. If you need access to the building for any reason on Monday, please contact the facilities department by Thursday to arrange access.",
                "question": "What are employees asked to do by Friday?",
                "choices": [
                    "A) Contact the facilities department",
                    "B) Back up their files to the cloud",
                    "C) Complete all pending projects",
                    "D) Report to a different office"
                ],
                "correct": "B",
                "explanation": "「金曜日の夕方までにデジタルファイルをクラウドサーバーに保存してください」と指示しています。Bが正解。",
                "skill_focus": "アナウンスメントの詳細理解"
            },
        ],
    },
}


TOEIC_READING = {
    "part5": {
        "easy": [
            {
                "sentence": "All employees are required to submit their expense reports ______ the end of each month.",
                "choices": ["A) by", "B) until", "C) for", "D) since"],
                "correct": "A",
                "explanation": "期限を表す場合は by（～までに）を使います。until は「～まで（ずっと）」で意味が異なる。",
                "grammar_point": "前置詞 by vs until"
            },
            {
                "sentence": "The marketing team presented a ______ analysis of consumer trends at the board meeting.",
                "choices": ["A) comprehend", "B) comprehension", "C) comprehensive", "D) comprehensively"],
                "correct": "C",
                "explanation": "名詞 analysis を修飾するのは形容詞 comprehensive（包括的な）。",
                "grammar_point": "品詞の選択（形容詞）"
            },
        ],
        "medium": [
            {
                "sentence": "The merger between the two companies is expected to be ______ by the end of the fiscal year.",
                "choices": ["A) finalize", "B) finalizing", "C) finalized", "D) finally"],
                "correct": "C",
                "explanation": "be動詞の後で受動態を作るのは過去分詞 finalized。「合併は完了される見込み」。",
                "grammar_point": "受動態"
            },
            {
                "sentence": "______ the contract is signed, construction on the new facility will begin immediately.",
                "choices": ["A) Once", "B) During", "C) While", "D) Until"],
                "correct": "A",
                "explanation": "「契約が締結されたら直ちに」という意味で Once（いったん〜したら）が正解。",
                "grammar_point": "接続詞の選択"
            },
        ],
        "hard": [
            {
                "sentence": "The board of directors voted ______ to approve the new sustainability initiative proposed by the CEO.",
                "choices": ["A) unanimous", "B) unanimity", "C) unanimously", "D) unanimousness"],
                "correct": "C",
                "explanation": "動詞 voted を修飾するのは副詞 unanimously（満場一致で）。",
                "grammar_point": "品詞の選択（副詞）"
            },
        ],
    },
}


# ====================================================================
# TOEFL iBT
# ====================================================================

TOEFL_IBT_LISTENING = {
    "conversation": {
        "medium": [
            {
                "dialogue": "M: Hi, Professor Chen. I wanted to talk to you about my research proposal for the independent study.\nW: Of course. Have you narrowed down your topic?\nM: I'm interested in the impact of urbanization on bird migration patterns, but I'm not sure if the scope is too broad.\nW: It is quite broad. You might consider focusing on a specific metropolitan area or a particular bird species. That would make your data collection much more manageable.\nM: That's a good point. Maybe I could focus on how the expansion of the Chicago metropolitan area has affected the migratory behavior of the common nighthawk.",
                "question": "Why does the student visit the professor?",
                "choices": [
                    "A) To ask about a grade on an exam",
                    "B) To discuss narrowing his research topic",
                    "C) To request a deadline extension",
                    "D) To report on his completed research"
                ],
                "correct": "B",
                "explanation": "学生は独立研究の提案について相談し、トピックが広すぎるかどうかを教授に確認しています。Bが正解。",
                "skill_focus": "学生と教授のオフィスアワー会話"
            },
        ],
    },
    "lecture": {
        "hard": [
            {
                "dialogue": "Today we're going to look at a fascinating area of marine biology—bioluminescence, or the production of light by living organisms. Now, bioluminescence is surprisingly common in the deep ocean. In fact, it's estimated that about 76 percent of ocean organisms are bioluminescent. The light is produced through a chemical reaction involving a molecule called luciferin and an enzyme called luciferase. When luciferin is oxidized by luciferase, energy is released in the form of light. Different organisms produce different colors of light, from blue and green in the deep sea to red in certain deep-water fish. But why would an organism want to produce light in the darkness of the deep ocean? Well, there are several adaptive advantages. Some species use it for counter-illumination—they light up their undersides to match the dim light from above, effectively becoming invisible to predators looking up from below.",
                "question": "According to the professor, what is counter-illumination used for?",
                "choices": [
                    "A) Attracting prey in the deep ocean",
                    "B) Communicating with other organisms",
                    "C) Camouflaging against predators by matching overhead light",
                    "D) Warning predators to stay away"
                ],
                "correct": "C",
                "explanation": "カウンターイルミネーションは「下面を照らして上方からの薄い光と一致させ、下から見上げる捕食者から見えなくなる」と説明されています。Cが正解。",
                "skill_focus": "学術講義の具体的概念理解"
            },
        ],
    },
}


# ====================================================================
# 英検
# ====================================================================

EIKEN_QUESTIONS = {
    "grade2": {
        "reading": [
            {
                "sentence": "The city council decided to ______ the old library building rather than tear it down, preserving its historical value.",
                "choices": ["A) renovate", "B) abandon", "C) demolish", "D) neglect"],
                "correct": "A",
                "explanation": "「取り壊すのではなく歴史的価値を保存する」という文脈から、renovate（改修する）が正解。",
                "skill_focus": "語彙（文脈からの推測）"
            },
            {
                "sentence": "Recent studies have shown that regular exercise can significantly ______ the risk of developing heart disease.",
                "choices": ["A) increase", "B) reduce", "C) maintain", "D) ignore"],
                "correct": "B",
                "explanation": "運動が心臓病リスクを「減らす」という一般的な知識と文脈からreduce が正解。",
                "skill_focus": "語彙（コロケーション）"
            },
        ],
        "listening": [
            {
                "dialogue": "M: Excuse me, I'd like to return this jacket. It doesn't fit properly.\nW: I'm sorry to hear that. Do you have the receipt?\nM: Yes, here it is.\nW: Would you like an exchange or a refund?",
                "question": "What will the man probably do next?",
                "choices": [
                    "A) Buy another jacket in a different size",
                    "B) Choose between an exchange or getting his money back",
                    "C) Leave the store without the jacket",
                    "D) Try the jacket on again"
                ],
                "correct": "B",
                "explanation": "店員が「交換か返金か」を尋ねているので、男性は次にそのどちらかを選ぶはず。Bが正解。",
                "skill_focus": "次の行動の予測"
            },
        ],
    },
    "pre1": {
        "reading": [
            {
                "sentence": "The CEO's abrupt resignation sent ______ through the company, as no successor had been named.",
                "choices": ["A) shockwaves", "B) compliments", "C) invitations", "D) advertisements"],
                "correct": "A",
                "explanation": "CEO の突然の辞任で会社に動揺が走ったという文脈から shockwaves が正解。",
                "skill_focus": "語彙（上級表現）"
            },
        ],
    },
}


# ====================================================================
# IELTS
# ====================================================================

IELTS_LISTENING = {
    "section1": {
        "medium": [
            {
                "dialogue": "W: Good morning, Riverside Sports Centre. How can I help you?\nM: Hi, I'd like to inquire about swimming lessons for adults.\nW: Certainly. We offer beginner, intermediate, and advanced classes. They run on Tuesday and Thursday evenings from 7 to 8 PM.\nM: I'm a complete beginner. How much do the lessons cost?\nW: The beginner course is 12 sessions for 85 pounds, and that includes pool access on weekends.",
                "question": "How much does the beginner swimming course cost?",
                "choices": [
                    "A) 58 pounds",
                    "B) 85 pounds",
                    "C) 120 pounds",
                    "D) 80 pounds"
                ],
                "correct": "B",
                "explanation": "女性が「ビギナーコースは12セッションで85ポンド」と明確に述べています。Bが正解。",
                "skill_focus": "日常場面での具体的情報の聞き取り"
            },
        ],
    },
    "section3": {
        "hard": [
            {
                "dialogue": "M: Professor, I've been reading about the urban heat island effect for my dissertation, and I'm finding conflicting data about its primary causes.\nW: That's not uncommon in this field. The relative contribution of factors like reduced vegetation, waste heat from buildings, and dark surfaces varies greatly depending on the city and climate zone.\nM: So would you suggest I focus on one specific factor?\nW: I'd recommend a comparative approach—look at how the relative importance of each factor changes across different urban contexts.",
                "question": "What approach does the professor recommend?",
                "choices": [
                    "A) Studying only one factor in depth",
                    "B) Comparing how different factors vary across cities",
                    "C) Ignoring the conflicting data",
                    "D) Focusing only on tropical cities"
                ],
                "correct": "B",
                "explanation": "教授は「比較アプローチ」を勧め、各要因の相対的重要度が都市の文脈によってどう変わるかを見ることを提案しています。Bが正解。",
                "skill_focus": "アカデミックな議論の理解"
            },
        ],
    },
}


# ====================================================================
# ユーティリティ
# ====================================================================

def get_test_questions(test_type, section, difficulty, q_type="all"):
    """テスト種別・セクション・難易度に応じた問題を返す"""
    
    # 難易度マッピング
    diff_map = {
        "易しい": "easy", "やや易しい": "easy",
        "標準": "medium",
        "やや難しい": "hard", "難しい": "hard",
    }
    diff_key = diff_map.get(difficulty, "medium")
    
    if test_type == "toefl_itp":
        return _get_toefl_itp_question(section, diff_key, q_type)
    elif test_type == "toeic":
        return _get_toeic_question(section, diff_key, q_type)
    elif test_type == "toefl_ibt":
        return _get_toefl_ibt_question(section, diff_key, q_type)
    elif test_type == "eiken":
        return _get_eiken_question(section, diff_key, q_type)
    elif test_type == "ielts":
        return _get_ielts_question(section, diff_key, q_type)
    
    return _fallback_question()


def _get_toefl_itp_question(section, difficulty, q_type):
    if section == "listening":
        sub = q_type if q_type in ["short_conversation", "lecture"] else random.choice(["short_conversation", "lecture"])
        bank = TOEFL_ITP_LISTENING.get(sub, {})
        pool = bank.get(difficulty, bank.get("medium", []))
        if pool:
            return random.choice(pool)
    
    elif section == "structure":
        sub = q_type if q_type in ["sentence_completion", "error_identification"] else random.choice(["sentence_completion", "error_identification"])
        bank = TOEFL_ITP_STRUCTURE.get(sub, {})
        pool = bank.get(difficulty, bank.get("medium", []))
        if pool:
            return random.choice(pool)
    
    elif section == "reading":
        bank = TOEFL_ITP_READING
        pool = bank.get(difficulty, bank.get("medium", []))
        if pool:
            passage_data = random.choice(pool)
            if passage_data.get("questions"):
                q = random.choice(passage_data["questions"])
                q["passage"] = passage_data["passage"]
                return q
    
    return _fallback_question()


def _get_toeic_question(section, difficulty, q_type):
    if section == "listening":
        sub = f"part{q_type}" if q_type in ["1", "2", "3", "4"] else random.choice(["part2", "part3", "part4"])
        bank = TOEIC_LISTENING.get(sub, {})
        pool = bank.get(difficulty, bank.get("medium", []))
        if pool:
            return random.choice(pool)
    
    elif section == "reading":
        bank = TOEIC_READING.get("part5", {})
        pool = bank.get(difficulty, bank.get("medium", []))
        if pool:
            q = random.choice(pool)
            if "sentence" in q and "question" not in q:
                q["question"] = "Choose the best word or phrase to complete the sentence."
            return q
    
    return _fallback_question()


def _get_toefl_ibt_question(section, difficulty, q_type):
    if section == "listening":
        sub = random.choice(["conversation", "lecture"])
        bank = TOEFL_IBT_LISTENING.get(sub, {})
        pool = bank.get(difficulty, bank.get("medium", []))
        if pool:
            return random.choice(pool)
    
    elif section == "reading":
        bank = TOEFL_ITP_READING  # 共有
        pool = bank.get(difficulty, bank.get("medium", []))
        if pool:
            passage_data = random.choice(pool)
            if passage_data.get("questions"):
                q = random.choice(passage_data["questions"])
                q["passage"] = passage_data["passage"]
                return q
    
    return _fallback_question()


def _get_eiken_question(section, difficulty, q_type):
    grade = "pre1" if difficulty == "hard" else "grade2"
    bank = EIKEN_QUESTIONS.get(grade, {})
    
    if section in ["reading", "listening"]:
        pool = bank.get(section, [])
        if pool:
            return random.choice(pool)
    
    return _fallback_question()


def _get_ielts_question(section, difficulty, q_type):
    if section == "listening":
        sub = "section3" if difficulty == "hard" else "section1"
        bank = IELTS_LISTENING.get(sub, {})
        pool = bank.get(difficulty, bank.get("medium", []))
        if pool:
            return random.choice(pool)
    
    return _fallback_question()


def _fallback_question():
    """汎用フォールバック問題"""
    return {
        "sentence": "The conference ______ postponed due to the severe weather conditions.",
        "question": "Choose the best answer.",
        "choices": ["A) was", "B) were", "C) has", "D) have"],
        "correct": "A",
        "explanation": "The conference は単数主語なので was が正解。受動態 was postponed。",
    }
