from common.constants import SkillCode, SkillLevel

SKILL_LEARNING_RULES = {
    SkillCode.LISTENING_PICTURE: {
        SkillLevel.BEGINNER: ['LESSON', 'PRACTICE'],
        SkillLevel.ELEMENTARY: ['PRACTICE', 'QUIZ'],
        SkillLevel.INTERMEDIATE: ['PRACTICE', 'QUIZ'],
        SkillLevel.ADVANCED: ['QUIZ'],
    },

    SkillCode.LISTENING_QA: {
        SkillLevel.BEGINNER: ['LESSON', 'PRACTICE'],
        SkillLevel.ELEMENTARY: ['PRACTICE', 'QUIZ'],
        SkillLevel.INTERMEDIATE: ['QUIZ'],
        SkillLevel.ADVANCED: ['QUIZ'],
    },

    SkillCode.LISTENING_CONVERSATION: {
        SkillLevel.BEGINNER: ['LESSON'],
        SkillLevel.ELEMENTARY: ['LESSON', 'PRACTICE'],
        SkillLevel.INTERMEDIATE: ['PRACTICE', 'QUIZ'],
        SkillLevel.ADVANCED: ['QUIZ'],
    },

    SkillCode.LISTENING_INFORMATION: {
        SkillLevel.BEGINNER: ['LESSON'],
        SkillLevel.ELEMENTARY: ['LESSON', 'PRACTICE'],
        SkillLevel.INTERMEDIATE: ['PRACTICE', 'QUIZ'],
        SkillLevel.ADVANCED: ['QUIZ'],
    },

    SkillCode.READING_SENTENCE: {
        SkillLevel.BEGINNER: ['LESSON', 'PRACTICE'],
        SkillLevel.ELEMENTARY: ['PRACTICE', 'QUIZ'],
        SkillLevel.INTERMEDIATE: ['QUIZ'],
        SkillLevel.ADVANCED: ['QUIZ'],
    },

    SkillCode.READING_TEXT: {
        SkillLevel.BEGINNER: ['LESSON'],
        SkillLevel.ELEMENTARY: ['PRACTICE'],
        SkillLevel.INTERMEDIATE: ['PRACTICE', 'QUIZ'],
        SkillLevel.ADVANCED: ['QUIZ'],
    },

    SkillCode.READING_PASSAGE: {
        SkillLevel.BEGINNER: ['LESSON', 'PRACTICE'],
        SkillLevel.ELEMENTARY: ['PRACTICE', 'QUIZ'],
        SkillLevel.INTERMEDIATE: ['PRACTICE', 'QUIZ'],
        SkillLevel.ADVANCED: ['QUIZ', 'MOCK'],
    },
}